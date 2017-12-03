#!/usr/bin/python

from __future__ import print_function # for python 2 compatibility
import hackathon_protocol
import os
import pandas as pd
import pickle
import xgboost

USERNAME="ML_anarchists"
PASSWORD="123456"

CONNECT_IP = os.environ.get("HACKATHON_CONNECT_IP") or "127.0.0.1"
CONNECT_PORT = int(os.environ.get("HACKATHON_CONNECT_PORT") or 12345)


class MyClient(hackathon_protocol.Client):
    def __init__(self, sock):
        super(MyClient, self).__init__(sock)
        self.counter = 0
        self.target_instrument = 'TEA'
        self.send_login(USERNAME, PASSWORD)
        self.last_raw = None
        self.stor = [[0, 0]]

        # Load pre-trained model previously created by create_model.ipynb
        self.model = pickle.load(open('./my_model.txt', 'rb'))

    def on_header(self, csv_header):
        self.header = {column_name: n for n, column_name in enumerate(csv_header)}
        #print("Header:", self.header)

    def on_orderbook(self, cvs_line_values):
        data = []
                
        bid_ps = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        bid_vs = [3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
        ask_ps = [22, 24, 26, 28, 30, 32, 34, 36, 38, 40]
        ask_vs = [23, 25, 27, 29, 31, 33, 35, 37, 39, 41]
        
        data = [cvs_line_values[i] for i in bid_ps[1:]+ask_ps[1:]]
        
        t_sum_1 = sum([cvs_line_values[i]*cvs_line_values[i+1] for i in bid_ps])
        t_sum_2 = sum([cvs_line_values[i]*cvs_line_values[i+1] for i in ask_ps])
        
        data.append( t_sum_1 / t_sum_2 )
        data.append( t_sum_1 - t_sum_2 )
        data.append( sum([cvs_line_values[i] for i in bid_vs]) / sum([cvs_line_values[i] for i in ask_vs]) )
            
        if cvs_line_values[0]=='TEA':
            try:
                data.append( cvs_line_values[4]-self.stor[0][0] )
                data.append( cvs_line_values[24]-self.stor[0][1] )
            except:
                print('!!!')
                self.stor.append( [cvs_line_values[4], cvs_line_values[24]] )
        else:
            data.append( 0 )
            data.append( 0 )
        #print('1', len(self.stor), len(data))
        if len(self.stor)==1000:
            self.stor = self.stor[1:][:]
        #print('2', len(self.stor), len(data))
        self.last_raw = data
        
    def make_prediction(self):
        assert self.last_raw is not None
        prediction = self.model.predict([self.last_raw])
        answer = prediction[0]
        self.send_volatility(float(answer))
        self.last_raw = None

    def on_score(self, items_processed, time_elapsed, score_value):
        print("Completed! items processed: %d, time elapsed: %.3f sec, score: %.6f" % (items_processed, time_elapsed, score_value))
        self.stop()


def on_connected(sock):
    client = MyClient(sock)
    client.run()


def main():
    hackathon_protocol.tcp_connect(CONNECT_IP, CONNECT_PORT, on_connected)


if __name__ == '__main__':
    main()
