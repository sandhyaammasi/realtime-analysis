# In order to run this example script successfully, the Intan RHX software
# should first be started, and through Network -> Remote TCP Control:

# Command Output should open a connection at 127.0.0.1, Port 5000.
# Status should read "Pending"

# Waveform Output (in the Data Output tab) should open a connection at 127.0.0.1, Port 5001.
# Status should read "Pending" for the Waveform Port (Spike Port is unused for this example,pytho
# and can be left disconnected)

# Once these ports are opened, this script can be run to acquire ~1 second of wideband data from channel A-010,
# which can then be plotted assuming "matplotlib" is installed


from ctypes import sizeof
import time, socket
from tkinter import Variable
import seaborn as sns
import numpy as np




# In order to plot the data, 'matplotlib' is required.
# If plotting is not needed, calls to plt can be removed and the data
# will still be present within the ReadWaveformDataDemo() function.
# 'matplotlib' can be installed with the command 'pip install matplotlib'

# the code is modified
import matplotlib.pyplot as plt

def readUint32(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 4]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=False)
    arrayIndex = arrayIndex + 4
    return variable, arrayIndex

def readInt32(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 4]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=True)
    arrayIndex = arrayIndex + 4
    return variable, arrayIndex

def readUint16(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 1]
    variable = int.from_bytes(variableBytes, byteorder='little', signed=False)
    arrayIndex = arrayIndex + 1
    return variable, arrayIndex

def readChar(array, arrayIndex):
    variableBytes = array[arrayIndex : arrayIndex + 5]
    variable = variableBytes.decode()
    arrayIndex = arrayIndex + 5    
    return variable,arrayIndex


def ReadSpikeDataDemo():

    # Declare buffer size for reading from TCP command socket
    # This is the maximum number of bytes expected for 1 read. 1024 is plenty for a single text command
    COMMAND_BUFFER_SIZE = 1024 # Increase if many return commands are expected

    # Declare buffer size for reading from TCP waveform socket.
    # This is the maximum number of bytes expected for 1 read

    # There will be some TCP lag in both starting and stopping acquisition, so the exact number of data blocks may vary slightly.
    # At 30 kHz with 1 channel, 1 second of wideband waveform data is 181,420 byte. See 'Calculations for accurate parsing' for more details
    # To allow for some TCP lag in stopping acquisition resulting in slightly more than 1 second of data, 200000 should be a safe buffer size
    WAVEFORM_BUFFER_SIZE = 200000 # Increase if channels, filter bands, or acquisition time increase

    # Connect to TCP command server - default home IP address at port 5000
    print('Connecting to TCP command server...')
    scommand = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    scommand.connect(('127.0.0.1', 5000))

    # Connect to TCP waveform server - default home IP address at port 5001
    print('Connecting to TCP waveform server...')
    swaveform = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    swaveform.connect(('127.0.0.1', 5002))

    # Query runmode from RHX software
    scommand.sendall(b'get runmode')
    commandReturn = str(scommand.recv(COMMAND_BUFFER_SIZE), "utf-8")

    '''isStopped = commandReturn == "Return: RunMode Stop"

    # If controller is running, stop it
    if not isStopped:
        scommand.sendall(b'set runmode stop')
        time.sleep(0.1) # Allow time for RHX software to accept this command before the next one comes
    '''
    
    # Query sample rate from RHX software
    scommand.sendall(b'get sampleratehertz')
    #commandReturn = str(scommand.recv(COMMAND_BUFFER_SIZE), "utf-8")
    scommand.recv(COMMAND_BUFFER_SIZE).decode("utf-8")
    '''expectedReturnString = "Return: SampleRateHertz "
    if commandReturn.find(expectedReturnString) == -1: # Look for "Return: SampleRateHertz N" where N is the sample rate
        raise Exception('Unable to get sample rate from server')
    else:
        sampleRate = float(commandReturn[len(expectedReturnString):])

    # Calculate timestep from sample rate
    timestep = 1 / sampleRate'''

    # Clear TCP data output to ensure no TCP channels are enabled
    scommand.sendall(b'execute clearalldataoutputs')
    time.sleep(0.1)

    # Send TCP commands to set up TCP Data Output Enabled for SPK
    # band of input channels
  
    tcpCommandSPKchannel = "set A-007.tcpdataoutputenabledspike true;".encode("utf-8")
    scommand.sendall(tcpCommandSPKchannel)
    time.sleep(0.1)



    spikeBytesPerBlock = 14
    while True:
        # Run controller for 1 second
        scommand.sendall(b'set runmode run')
        #time.sleep(2)
        

        # Read waveform data
        rawData = swaveform.recv(WAVEFORM_BUFFER_SIZE)

        if len(rawData) % spikeBytesPerBlock != 0:
            raise Exception('An unexpected amount of data arrived that is not an integer multiple of the expected data size per block')

        numBlocks = int((len(rawData) / spikeBytesPerBlock))

        rawIndex = 0 # Index used to read the raw data that came in through the TCP socket
        spikeTimestamp = [] # List used to contain scaled timestamp values in seconds
        spikeCount = 0
        SPKchannelArray =[]

        '''#get channel name when dealing with just one channel
        channelName = rawData[4:9]
        print(channelName.decode()) '''

        for block in range(numBlocks):
            # Expect 4 bytes to be TCP Magic Number as uint32.
            # If not what's expected, raise an exception.
            magicNumber, rawIndex = readUint32(rawData, rawIndex)
        
            if magicNumber != 0x3ae2710f:
                raise Exception('Error... magic number incorrect')

            #   skipping 5 bytes for channel name
            #rawIndex = rawIndex + 5   
            
            #reading channel that has spike and appending it
            SPKchannel, rawIndex =readChar(rawData,rawIndex)
            if SPKchannel not in SPKchannelArray:
                SPKchannelArray.append(SPKchannel) 

            # Expect 4 bytes to be timestamp as int32.
            rawTimestamp, rawIndex = readInt32(rawData, rawIndex)

            # append timestamp of every spike to the spikeTimestamp list
            spikeTimestamp.append(rawTimestamp)
            print(rawTimestamp)
            #    Expect 1 bytes of spike ID - it's always 1 hence skipping the next line and simply incrementing the rawIndex by 1
            #   spikeID, rawIndex = readUint16(rawData, rawIndex)  
            rawIndex = rawIndex + 1
            # append spikeID of every spike to the spikeIDarray list
            spikeCount = spikeCount + 1


           

    scommand.sendall(b'set runmode stop')
    print("amplifier Timestamps", spikeTimestamp)

ReadSpikeDataDemo()