import web
import time
from datetime import datetime
import board
import adafruit_si7021
import matplotlib.pyplot as plt
import pandas as pd
import sched
import os
from multiprocessing import Process

render = web.template.render('templates/')
urls = ('/', 'Index')
sensor = adafruit_si7021.SI7021(board.I2C())

s = sched.scheduler(time.time, time.sleep)

class Index:
    def GET(self):
        humidity = Get_Humidity()
        temperature = ((9/5)*float(sensor.temperature)) + 32 #  temp in fahrenheit
        return(render.index(humidity, temperature))

def Get_Humidity():
    return sensor.relative_humidity

def Run_Web_Server():
    app = web.application(urls, globals())
    app.run()

def Make_Graph():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    df = pd.read_csv('humidity.csv', sep=",")
    data = df.tail(60)

    plt.plot(data['time'], data['humidity'])
    plt.xticks(rotation=45, ha='right', ticks=[59,0])
    plt.subplots_adjust(bottom=0.30)
    plt.title('Humidity Graph for Last Hour')
    plt.ylabel('Humidity (%)')
    plt.xlabel('Time (last hour)')
    plt.savefig('static/humidity_graph.png')
    plt.close(fig)

def Write_Humidity_Graph(sc):
    humidity = ('{0:1f}'.format(Get_Humidity()))

    #   writes to humidity.csv
    with open('humidity.csv', 'a') as logfile:
        logfile.write(f'{datetime.now().strftime("%H:%M")}, {str(humidity)}\n')

    Make_Graph()
    s.enter(60, 1, Write_Humidity_Graph, (sc,))

def Check_CSV():
    if os.path.exists('humidity.csv',):
        Check_CSV_Len()
    else:
        with open('humidity.csv', 'w') as f:
            f.write('time,humidity\n')

def Check_CSV_Len():
    with open('humidity.csv') as f:
        line_count = sum(1 for line in f)
        if line_count >= 7200:
            os.remove('humidity.csv')
    Check_CSV()

def Run_Logging():
    Check_CSV()
    s.enter(60, 1, Write_Humidity_Graph, (s,))
    s.run()

def Run_In_Parallel(*fns):
    proc = []
    for fn in fns:
       p = Process(target=fn)
       p.start()
       proc.append(p)
    for p in proc:
        p.join()

if __name__ == '__main__':
   Run_In_Parallel(Run_Web_Server, Run_Logging)