#!/usr/bin/python
# Filename: online-analysis-example.py
import os
import sys
from collections import deque

# Import MobileInsight modules
from mobile_insight.analyzer import *
from mobile_insight.monitor import OnlineMonitor

def greaterThan(time1, time2):
    if time1['HSFN'] > time2['HSFN']:
        return True
    elif time1['HSFN'] < time2['HSFN']:
        return False
    if time1['SFN'] > time2['SFN']:
        return True
    elif time1['SFN'] < time2['SFN']:
        return False
    if time1['SubFN'] > time2['SubFN']:
        return True
    return False

class TestAnalyzer(Analyzer):
    def __init__(self):
        Analyzer.__init__(self)
        self.add_source_callback(self.__msg_callback)
        self.bufferqueue = deque()
        self.timer = 0
        self.prevbytedata = 0 # setup for no possibility
        self.latencyInfo = []
        self.currLatencyCount = 0
        self.DCITimeInfo = []

        self.HFN = 0 # Hyper FN clock
        self.prevFN = 0
        self.recentupdateTime = 0
        # print ("test")

        #DL latency timestamps
        self.DCI_time = []
        self.PDSCH_time = []

    def set_source(self, source):
        Analyzer.set_source(self, source)
        source.enable_log_all()
        #src.enable_log("LTE_PHY_PUSCH_Tx_Report")
        #src.enable_log("LTE_MAC_UL_Buffer_Status_Internal")
        #src.enable_log("LTE_NB1_ML1_GM_DCI_Info")
        # source.enable_log("LTE_RRC_OTA_Packet")
        # source.enable_log("LTE_NAS_ESM_Plain_OTA_Incoming_Message")
        # source.enable_log("LTE_NAS_ESM_Plain_OTA_Outgoing_Message")
        # source.enable_log("LTE_NAS_EMM_Plain_OTA_Incoming_Message")
        # source.enable_log("LTE_NAS_EMM_Plain_OTA_Outgoing_Message")
        

    def __msg_callback(self, msg):
        # print ("ok")
        #if msg.type_id == "LTE_MAC_UL_Buffer_Status_Internal":
            #print(msg.data.decode())
        #if msg.type_id == "LTE_MAC_UL_Buffer_Status_Internal":
        if False:
            bytedata = 0
            for packet in msg.data.decode()['Subpackets']:
                # print (msg.data.decode()['timestamp'])
                for sample in packet['Samples']:
                    self.timer += 1

                    SFN = sample['Sub FN']
                    FN = sample['Sys FN']
                    LCIDcount = sample['Number of active LCID']
                    LCID = sample['LCIDs']

                    # update on hyper FN
                    if FN < self.prevFN:
                        self.HFN += 1
                        self.recentupdateTime = msg.data.decode()['timestamp']

                    for i in range(LCIDcount): 
                        bytedata = LCID[i]['Total Bytes']

                    if self.prevbytedata < bytedata: 
                        self.bufferqueue.append([bytedata - self.prevbytedata, bytedata - self.prevbytedata, self.timer])
                    
                    if self.prevbytedata >= bytedata and self.prevbytedata > 0: 
                        # data is sending out
                        outdata = self.prevbytedata - bytedata


                        # data sent out and one buffer is cleared
                        while len(self.bufferqueue) > 0 and self.bufferqueue[0][0] <= outdata: 
                            Latency = self.timer - self.bufferqueue[0][2]
                            print("\t", Latency,"\t" ,self.bufferqueue[0][1])
                            # correct timestamp for FN and SFN info here
                            self.latencyInfo.append([Latency, self.bufferqueue[0][0], FN, SFN, self.HFN])
                            
                            # store latency, data size, finished time
                            outdata -= self.bufferqueue[0][0]
                            self.bufferqueue.popleft()
                            
                        # when data are sent out but buffer not yet empty
                        if outdata > 0: 
                            self.bufferqueue[0][0] -= outdata

                    
                    self.prevbytedata = bytedata
                    self.prevFN = FN

        #return
        time = {}
        if msg.type_id == "LTE_NB1_ML1_GM_DCI_Info": 
            #print(msg.data.decode())
            for record in msg.data.decode()['Records']:
                if record['DL Grant Present'] == 'True':
                    time['HSFN'] = record['NPDCCH Timing HSFN']
                    time['SFN'] = record['NPDCCH Timing SFN']
                    time['SubFN'] = record['NPDCCH Timing Sub FN']
                    print('DCI', time,'\n')
                    self.DCI_time.append(time)
        if msg.type_id == 'LTE_NB1_ML1_GM_PDSCH_STAT_Ind':
            #print(msg.data.decode())
            for record in msg.data.decode()['Records']:
                time['HSFN'] = record['Hyper SFN Data'] 
                time['SFN'] = record['SFN']
                time['SubFN'] = record['Sub FN'] 
                print('PDSCH',time,'\n')
                self.PDSCH_time.append(time)
        for i in range(len(self.DCI_time)):
            match = False
            for j in range(len(self.PDSCH_time)):
                p_time = self.PDSCH_time[j]
                d_time = self.DCI_time[i]
                if greaterThan(p_time, d_time):
                    #print('latency:', 10*(p_time['']-d_time[1]) + p_time[2]-d_time[2])
                    print(d_time)
                    print(p_time,'\n')
                    self.PDSCH_time.pop(j)
                    match = True
                    break
            if match:
                self.DCI_time.pop(i)
                break
if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Error: please specify physical port name and baudrate.")
        print((__file__, "SERIAL_PORT_NAME BAUNRATE"))
        sys.exit(1)

    # Initialize a 3G/4G monitor
    src = OnlineMonitor()
    src.set_serial_port(sys.argv[1])  # the serial port to collect the traces
    src.set_baudrate(int(sys.argv[2]))  # the baudrate of the port

    # Enable 3G/4G RRC (radio resource control) monitoring
    # src.enable_log("LTE_RRC_OTA_Packet")
    # src.enable_log("WCDMA_RRC_OTA_Packet")
    src.enable_log_all()
    # src.enable_log("LTE_PHY_PUSCH_Tx_Report")
    #src.enable_log("LTE_MAC_UL_Buffer_Status_Internal")
    #src.enable_log("LTE_NB1_ML1_GM_DCI_Info")


    # 4G RRC analyzer
    # lte_rrc_analyzer = LteRrcAnalyzer()
    # lte_rrc_analyzer.set_source(src)  # bind with the monitor
    test_analyzer = TestAnalyzer()
    test_analyzer.set_source(src)

    # 3G RRC analyzer
    # wcdma_rrc_analyzer = WcdmaRrcAnalyzer()
    # wcdma_rrc_analyzer.set_source(src)  # bind with the monitor

    # Start the monitoring
    src.run()
