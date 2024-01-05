"""
Use of SimComponents to simulate the network of queues from Homework #6 problem 1, Fall 2014.
See corresponding solution set for mean delay calculation based on Burkes theorem.

Copyright 2014 Dr. Greg M. Bernstein
Released under the MIT license

The original code has been modified s.t.
(i)   user arguments are included to ease experimentation
(ii)  new simulation looks like Figure 1 as requested in the project specification

Answer for the first question was generated with:
```console
python ProjectCode2.py --port_rate=100 --buffer_size=100
python ProjectCode2.py --port_rate=100 --buffer_size=250
python ProjectCode2.py --port_rate=100 --buffer_size=500
python ProjectCode2.py --port_rate=100 --buffer_size=1000
python ProjectCode2.py --port_rate=100 --buffer_size=10000
python ProjectCode2.py --port_rate=100 --buffer_size=120000
python ProjectCode2.py --port_rate=500 --buffer_size=100
python ProjectCode2.py --port_rate=500 --buffer_size=250
python ProjectCode2.py --port_rate=500 --buffer_size=500
python ProjectCode2.py --port_rate=500 --buffer_size=1000
python ProjectCode2.py --port_rate=500 --buffer_size=10000
python ProjectCode2.py --port_rate=500 --buffer_size=120000
python ProjectCode2.py --port_rate=1000 --buffer_size=100
python ProjectCode2.py --port_rate=1000 --buffer_size=250
python ProjectCode2.py --port_rate=1000 --buffer_size=500
python ProjectCode2.py --port_rate=1000 --buffer_size=1000
python ProjectCode2.py --port_rate=1000 --buffer_size=10000
python ProjectCode2.py --port_rate=1000 --buffer_size=120000
python ProjectCode2.py --port_rate=2000 --buffer_size=100
python ProjectCode2.py --port_rate=2000 --buffer_size=250
python ProjectCode2.py --port_rate=2000 --buffer_size=500
python ProjectCode2.py --port_rate=2000 --buffer_size=1000
python ProjectCode2.py --port_rate=2000 --buffer_size=10000
python ProjectCode2.py --port_rate=2000 --buffer_size=120000
```
"""
import argparse
import random
import functools

import simpy

from SimComponents import PacketGenerator, PacketSink, SwitchPort, RandomBrancher

# Arguments for the script
parser = argparse.ArgumentParser(description='Script for Part 2.')
parser.add_argument('-rs', '--random_seed', default=29, type=int, help='Random seed for the simulation')
parser.add_argument('-pr', '--port_rate', default=1000, type=int, help='Port rate in packets per second')
parser.add_argument('-bs', '--buffer_size', default=120000, type=int, help='Buffer size in bytes')
parser.add_argument('-st', '--sim_time', default=4000, type=int, help='Simulation time')
args = parser.parse_args()

if __name__ == '__main__':
    # Set random seeds for reproducibility
    random.seed(args.random_seed)

    # Set up arrival and packet size distributions
    # Using Python functools to create callable functions for random variates with fixed parameters.
    # each call to these will produce a new random value.
    mean_pkt_size = 100.0  # in bytes
    adist1 = functools.partial(random.expovariate, 1.5)  # lambda_1
    adist2 = functools.partial(random.expovariate, 0.5)  # lambda_4
    adist3 = functools.partial(random.expovariate, 0.7)  # lambda_3 
    sdist = functools.partial(random.expovariate, 1.0 / mean_pkt_size)  # mean size is 100 bytes
    samp_dist = functools.partial(random.expovariate, 0.50)
    port_rate = args.port_rate * 8 * mean_pkt_size  # want a rate of args.port_rate packets per second

    # Create the SimPy environment. This is the thing that runs the simulation.
    env = simpy.Environment()

    # Create the packet generators and sink
    def selector(pkt):
        return pkt.src == "SJSU1"

    def selector2(pkt):
        return pkt.src == "SJSU2"
    ps1 = PacketSink(env, debug=False, rec_arrivals=True, selector=selector)
    ps2 = PacketSink(env, debug=False, rec_waits=True, selector=selector2)

    pg1 = PacketGenerator(env, "SJSU1", adist1, sdist)
    pg2 = PacketGenerator(env, "SJSU2", adist2, sdist)
    pg3 = PacketGenerator(env, "SJSU3", adist3, sdist)

    branch1 = RandomBrancher(env, [0.80, 0.20])  # 80% continue, 20% drop
    branch2 = RandomBrancher(env, [0.70, 0.30])  # 70% top branch, 30% bottom branch

    # Added qlimit=args.buffer_size to switch ports to enforce buffer size constraint
    switch_port1 = SwitchPort(env, port_rate, args.buffer_size)
    switch_port2 = SwitchPort(env, port_rate, args.buffer_size)
    switch_port3 = SwitchPort(env, port_rate, args.buffer_size)
    switch_port4 = SwitchPort(env, port_rate, args.buffer_size)
    
    # Wire packet generators, switch ports, and sinks together
    pg1.out = switch_port1
    switch_port1.out = branch1
    branch1.outs[0] = switch_port2

    switch_port2.out = branch2
    branch2.outs[0] = switch_port3
    branch2.outs[1] = switch_port4
    pg3.out = switch_port3
    pg2.out = switch_port4

    switch_port3.out = ps1
    switch_port4.out = ps2
    
    # Run it
    env.run(until=args.sim_time)
    
    print("average wait source 1 to output 3 = {}".format(sum(ps1.waits)/len(ps1.waits)))
    print("average wait source 2 to output 4 = {}".format(sum(ps2.waits)/len(ps2.waits)))
    print("packets sent {}".format(pg1.packets_sent))
    print("packets received: {}".format(len(ps1.waits) + len(ps2.waits)))
    print("packets dropped: {}".format(pg1.packets_sent - (len(ps1.waits) + len(ps2.waits))))
