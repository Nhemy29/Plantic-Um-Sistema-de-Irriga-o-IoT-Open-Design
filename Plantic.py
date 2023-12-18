from machine import Pin, ADC, Timer
from time import sleep_ms, ticks_ms, localtime, mktime
from requests import get
from umqtt.simple import MQTTClient
from network import WLAN, STA_IF
from ntptime import settime
from json import dumps, loads

bombinha = Pin(19, Pin.OUT, value=1)

def ativaWifi(rede, senha):
    wifi = WLAN(STA_IF)
    wifi.active(True)
    if not wifi.isconnected():
        wifi.connect(rede, senha)
        tentativas = 0
        while not wifi.isconnected() and tentativas < 10:
            sleep_ms(1000)
            tentativas += 1
    return wifi if wifi.isconnected() else None



def desliga_bomba(p):
    global bombinha

    bombinha.on()

def analise (t, c):
    global bombinha, carencia, lumi, umidade, temporizador
    if t == top1:
        bombinha.off()
        print(bombinha.value())
        print('app mandou irrigar')
        temporizador.init(period=2000, mode=Timer.ONE_SHOT, callback=desliga_bomba)
        carencia = ticks_ms() + 2000
    
    if t == top5:
        print("app mandou ver lumi e umidade")
        print(f'a luminosidade é {lumi}')
        jlumi=str(lumiporcento)
        respostalumi=jlumi.encode()
        cliente.publish(top4, respostalumi)

        print(f'a umidade é {umidadeporcento}')
        jumidade=str(umidadeporcento)
        respostaumidade=jumidade.encode()
        cliente.publish(top3, respostaumidade)

top1 = b'plantic/irrigar' 
top2 = b'plantic/+' 
top3 = b'plantic/irrigar/umidade' 
top4 = b'plantic/irrigar/luz' 
top5 = b'plantic/info' 

#conectar ao broker
Net = ativaWifi('joaozinho', '12345abCD') #TROCAR QUANDO NECESSARIO
cliente = MQTTClient('seguranca', 'broker.hivemq.com') # id, broker
cliente.set_callback(analise)
cliente.connect()
cliente.subscribe(top1)
cliente.subscribe(top5)


temperatura=0
carencia = 0

medicao = ADC(Pin(32))

temporizador = Timer(0)

luz = ADC(Pin(33))

tempo=ticks_ms() + 2000
dia=0
timeint=0
lumiporcento=0
umidadeporcento=0

while True:
    cliente.check_msg()
    umidade=medicao.read()
    lumi=luz.read()

    if umidade >= 0 and umidade < 300:
        umidadeporcento= 'Encharcado'
    elif umidade >= 300 and umidade < 600:
        umidadeporcento= 'Muita água'
    elif umidade >= 600 and umidade < 800:
        umidadeporcento= 'Acima do ideal'
    elif umidade >= 800 and umidade < 1500:
        umidadeporcento= 'Ideal'
    elif umidade >= 1500 and umidade < 2100:
        umidadeporcento= 'Médio'
    elif umidade >= 2100 and umidade < 3900:
        umidadeporcento= 'Quase seco'
    elif umidade >= 3900 and umidade < 4095:
        umidadeporcento= 'Seco'

    if lumi < 409.5:
        lumiporcento= "0% - 10%"
    elif lumi < 819:
        lumiporcento= "10% - 20%"
    elif lumi < 1228:
        lumiporcento= "20% - 30%"
    elif lumi < 1638:
        lumiporcento= "30% - 40%"
    elif lumi < 2047:
        lumiporcento= "40% - 50%"
    elif lumi < 2457:
        lumiporcento= "50% - 60%"
    elif lumi < 2866:
        lumiporcento= "60% - 70%"
    elif lumi < 3276:
        lumiporcento= "70% - 80%"
    elif lumi < 3685.5:
        lumiporcento= "80% - 90%"
    elif lumi < 4095:
        lumiporcento= "90% - 100%"
 
    if ticks_ms() > tempo:
       
        #busca os dados na web
        site = 'https://api.open-meteo.com/v1/forecast?latitude=-32.125&longitude=-52.125&timezone=auto&current_weather=true'
        M = get(site)
        napolitano = M.json()
        M.close()
        time = napolitano['current_weather']['time']
        timec = time.split("T")
        timecc= timec[1].split(":")
        timeint= int(timecc[0])
        print (f"umidade:{umidade}  hora:{timeint}H  luminosdade:{lumi}")
        tempo=ticks_ms() + 5000
        print(bombinha.value())
        

    if lumi < 3276 and umidade > 1600 and carencia < ticks_ms():
        if 19 >= timeint <=24 or 00 >= timeint <= 07:
            bombinha.off()
            print(bombinha.value())
            temporizador.init(period=500, mode=Timer.ONE_SHOT, callback=desliga_bomba)
            carencia = ticks_ms() + 600000
    

