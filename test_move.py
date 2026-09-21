import sys
sys.path.insert(0, '.')
import time

print("Você tem 3 segundos para clicar na janela do Katamari...")
time.sleep(3)

from pynput.keyboard import Controller
kb = Controller()

print("Pressionando W agora...")
kb.press('w')
time.sleep(2)
kb.release('w')
print("Soltou W")