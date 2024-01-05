"""
This is a simpy based  simulation of a M/M/1 queue system.

The original code has been modified s.t.
(i)   user arguments are included to ease experimentation
(ii)  the queue has a finite buffer specified by the `--buffer_size` flag
(iii) inter-arrival and service time can be made deterministic by setting `--time_distribution=constant`

Answer for the first question was generated with:
```console
python ProjectCode1.py --arrival_rates=0.1,0.2,0.4,0.8 --buffer_size=5 --time_distribution=poisson
python ProjectCode1.py --arrival_rates=0.1,0.2,0.4,0.8 --buffer_size=10 --time_distribution=poisson
python ProjectCode1.py --arrival_rates=0.1,0.2,0.4,0.8 --buffer_size=20 --time_distribution=poisson
python ProjectCode1.py --arrival_rates=0.1,0.2,0.4,0.8 --buffer_size=40 --time_distribution=poisson
```

Answer for the second question was generated with:
```console
python ProjectCode1.py --arrival_rates=0.1,0.2,0.4,0.8 --buffer_size=5 --time_distribution=constant
python ProjectCode1.py --arrival_rates=0.1,0.2,0.4,0.8 --buffer_size=10 --time_distribution=constant
python ProjectCode1.py --arrival_rates=0.1,0.2,0.4,0.8 --buffer_size=20 --time_distribution=constant
python ProjectCode1.py --arrival_rates=0.1,0.2,0.4,0.8 --buffer_size=40 --time_distribution=constant
```
"""

import random
import simpy
import math
import argparse

# Arguments for the script
parser = argparse.ArgumentParser(description='Script for Part 1.')
parser.add_argument('-rs', '--random_seed', default=29, type=int, help='Random seed for the simulation')
parser.add_argument('-ar', '--arrival_rates', default="0.1,0.2", type=str, help='A comma separated list of arrival rates, lambdas')
parser.add_argument('-st', '--sim_time', default=1000000, type=int, help='Simulation time')
parser.add_argument('-bs', '--buffer_size', default=20, type=int, help='Buffer size in packets')
parser.add_argument('-td', '--time_distribution', choices=['constant', 'poisson'], default='poisson', help='Time distribution for inter-arrival and service')
parser.add_argument('-mu', '--mu', default=2.0, type=float, help='Mu parameter for service time')
args = parser.parse_args()


""" Queue system  """
class server_queue:
    def __init__(self, env, arrival_rate, Packet_Delay, Server_Idle_Periods):
        self.server = simpy.Resource(env, capacity=1)
        self.env = env
        self.queue_len = 0
        self.flag_processing = 0
        self.packet_number = 0
        self.sum_time_length = 0
        self.start_idle_time = 0
        self.arrival_rate = arrival_rate
        self.Packet_Delay = Packet_Delay
        self.Server_Idle_Periods = Server_Idle_Periods


    def process_packet(self, env, packet):
        with self.server.request() as req:
            start = env.now
            yield req

            # service time of one packet
            if args.time_distribution == 'constant':
                yield env.timeout(args.mu)
            elif args.time_distribution == 'poisson':
                yield env.timeout(random.expovariate(1 / args.mu))
                # as mu specifies packets per second, to get seconds we take the reciprocal
                # random expovariate corresponds to the poisson distribution

            latency = env.now - packet.arrival_time
            self.Packet_Delay.addNumber(latency)
            # print("Packet number {0} with arrival time {1} latency {2}".format(packet.identifier, packet.arrival_time, latency))
            self.queue_len -= 1
            if self.queue_len == 0:
                self.flag_processing = 0
                self.start_idle_time = env.now

    def packets_arrival(self, env):
        # packet arrivals

        while True:
            # Infinite loop for generating packets

            # arrival time of one packet
            if args.time_distribution == 'constant':
                yield env.timeout(1 / self.arrival_rate)
            elif args.time_distribution == 'poisson':
                yield env.timeout(random.expovariate(self.arrival_rate))

            self.packet_number += 1
            # packet id -- also used to track total number of packets

            arrival_time = env.now
            new_packet = Packet(self.packet_number, arrival_time)
            if self.flag_processing == 0:
                self.flag_processing = 1
                idle_period = env.now - self.start_idle_time
                self.Server_Idle_Periods.addNumber(idle_period)
                # print("Idle period of length {0} ended".format(idle_period))

            # Only process the next packet if bugger size is not filled
            if self.queue_len < args.buffer_size:
                env.process(self.process_packet(env, new_packet))
                self.queue_len += 1


""" Packet class """
class Packet:
    def __init__(self, identifier, arrival_time):
        self.identifier = identifier
        self.arrival_time = arrival_time


class StatObject:
    def __init__(self):
        self.dataset =[]

    def addNumber(self,x):
        self.dataset.append(x)
    def sum(self):
        n = len(self.dataset)
        sum = 0
        for i in self.dataset:
            sum = sum + i
        return sum
    def mean(self):
        n = len(self.dataset)
        sum = 0
        for i in self.dataset:
            sum = sum + i
        return sum/n
    def maximum(self):
        return max(self.dataset)
    def minimum(self):
        return min(self.dataset)
    def count(self):
        return len(self.dataset)
    def median(self):
        self.dataset.sort()
        n = len(self.dataset)
        if n//2 != 0: # get the middle number
            return self.dataset[n//2]
        else: # find the average of the middle two numbers
            return ((self.dataset[n//2] + self.dataset[n//2 + 1])/2)
    def standarddeviation(self):
        temp = self.mean()
        sum = 0
        for i in self.dataset:
            sum = sum + (i - temp)**2
        sum = sum/(len(self.dataset) - 1)
        return math.sqrt(sum)


def main():
    print("Simple queue system model:mu = {0}".format(args.mu))
    print ("{0:<9} {1:<9} {2:<9} {3:<9} {4:<9} {5:<9} {6:<9} {7:<9} {8:<9} {9:<9}".format(
        "Lambda", "Count", "Min", "Max", "Mean", "Median", "Sd", "Utilization", "Num. Total", "Num. Dropped"))
    random.seed(args.random_seed)
    for arrival_rate in [float(r) for r in args.arrival_rates.split(',')]:
        env = simpy.Environment()
        Packet_Delay = StatObject()
        Server_Idle_Periods = StatObject()
        router = server_queue(env, arrival_rate, Packet_Delay, Server_Idle_Periods)
        env.process(router.packets_arrival(env))
        env.run(until=args.sim_time)
        print ("{0:<9.3f} {1:<9} {2:<9.3f} {3:<9.3f} {4:<9.3f} {5:<9.3f} {6:<9.3f} {7:<9.3f} {8:<9} {9:<9}".format(
            round(arrival_rate, 3),
            int(Packet_Delay.count()),
            round(Packet_Delay.minimum(), 3),
            round(Packet_Delay.maximum(), 3),
            round(Packet_Delay.mean(), 3),
            round(Packet_Delay.median(), 3),
            round(Packet_Delay.standarddeviation(), 3),
            round(1 - Server_Idle_Periods.sum() / args.sim_time, 3),
            int(router.packet_number),
            int(router.packet_number - Packet_Delay.count())))

if __name__ == '__main__': main()