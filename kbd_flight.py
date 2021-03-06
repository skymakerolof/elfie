#!/usr/local/bin/python3


import binascii
import curses
import drone
import pygame
import sys
import time


KEYS = {
  'start': pygame.K_p,
  'stop': pygame.K_o,

  'throttle_u': pygame.K_w,
  'throttle_d': pygame.K_s,
  'yaw_l': pygame.K_a,
  'yaw_r': pygame.K_d,
  'pitch_u': pygame.K_UP,
  'pitch_d': pygame.K_DOWN,
  'roll_l': pygame.K_LEFT,
  'roll_r': pygame.K_RIGHT,
}


DASHBOARD = """
 Flight control for Eachine/JJRC

            throttle                            pitch

               [w]                               [up]

              {throttle_u:>3}%                               {pitch_u:>3}%

 yaw [a] {yaw_l:>3}%      {yaw_r:>3}%  [d]         [left] {roll_l:>3}%      {roll_r:>3}%  [right]  roll

              {throttle_d:>3}%                               {pitch_d:>3}%

               [s]                              [down]


roll:{roll:>3} pitch:{pitch:>3} throttle:{throttle:>3} yaw:{yaw:>3}
pressed: {pressed_keys}
Command for drone: 0x{hex_command}

Unix time: {unixtime}

Press Ctrl+C to exit
"""


def init_screen():
  screen = curses.initscr()
  curses.noecho()
  # set getch() non-blocking
  screen.nodelay(1)
  # escape sequences generated by some keys (keypad, function keys) will be interpreted by curses
  screen.keypad(1)
  screen.clearok(1)
  return screen


def redraw_screen(screen, roll, pitch, throttle, yaw,
                  pressed=None, drone_command=''):
  if pressed is None:
      pressed = []

  state = {
    'throttle_u': int((throttle+1)/2.0*100),
    'throttle_d': int((1-(throttle+1)/2.0)*100),
    'yaw_r': int((yaw+1)/2.0*100),
    'yaw_l': int((1-(yaw+1)/2.0)*100),
    'pitch_u': int((pitch+1)/2.0*100),
    'pitch_d': int((1-(pitch+1)/2.0)*100),
    'roll_r': int((roll+1)/2.0*100),
    'roll_l': int((1-(roll+1)/2.0)*100),
    'unixtime': time.time(),
    'hex_command': binascii.hexlify(drone_command),
    'pressed_keys': str(pressed),
    'roll': roll,
    'pitch': pitch,
    'throttle': throttle,
    'yaw': yaw,
  }

  screen.clear()

  for i, line in enumerate(DASHBOARD.split('\n')):
    screen.addstr(i, 0, line.format(**state))

  screen.refresh()


def parse_input():
  roll, pitch, throttle, yaw = 0, 0, 0, 0
  commands = set()
  pressed = set()

  pressed_dict = pygame.key.get_pressed()
  for key, code in KEYS.items():
    if pressed_dict[code]:
      pressed.add(key)

  if 'start' in pressed:
    commands.add('spin_up')
  if 'stop' in pressed:
    commands.add('shut_off')

  if 'roll_l' in pressed:
    roll -= 1
  if 'roll_r' in pressed:
    roll += 1
  if 'pitch_d' in pressed:
    pitch -= 1
  if 'pitch_u' in pressed:
    pitch += 1
  if 'throttle_d' in pressed:
    throttle -= 1
  if 'throttle_u' in pressed:
    throttle += 1
  if 'yaw_l' in pressed:
    yaw -= 1
  if 'yaw_r' in pressed:
    yaw += 1

  return roll, pitch, throttle, yaw, commands, pressed


DEBUG = True
if DEBUG:
    MAX_POWER = 0.5


def main_loop(drone1, screen):
  try:
    while 1:
      roll, pitch, throttle, yaw, commands, pressed = parse_input()

      max_power = 1.0 if 'force' in commands else MAX_POWER

      if 'shut_off' in commands:
        cmd = 'shut_off'
      elif 'spin_up' in commands:
        cmd = 'spin_up'
      else:
        cmd = None

      pitch *= max_power
      roll *= max_power

      drone_command = drone.get_command_string(
        roll=roll, pitch=pitch, throttle=throttle, yaw=yaw,
        command=cmd, altitude_hold=True
      )
      drone1.execute(drone_command)

      pygame.event.pump()

      if screen is not None:
        redraw_screen(screen, roll, pitch, throttle, yaw,
                      pressed=pressed,
                      drone_command=drone_command)
      clock.tick(20)
  finally:
    drone1.disconnect()
    curses.endwin()

if __name__ == '__main__':
  drone1 = drone.Drone()
  pygame.init()
  screen = init_screen()
  kbd = None
  clock = pygame.time.Clock()
  main_loop(drone1, screen)
