#!/usr/bin/env python
# encoding: utf-8

"""
Game at: http://www.miniclip.com/games/sushi-go-round/en/

Coordinates set for a screen resolution of 1920x1080, and Chrome 
occupying the whole left half of the screen.

You only have to change Glob.window_topleft to get it to work 
with a different set-up.

Email me at rgfibe at gmail for comments or questions.

"""

import os 
import time 
import sys 
import autopy # control mouse and keyboard and capture screen.
import webbrowser  # open the browser to the game's website.
import threading # parallel thread sleeps to wait for food delivery.


class Glob:
# This class is just a dictionary for coordinates and pixel values.

    # Pixel ruler on full-screen capture to get game window coordinates.
    # (Actually you need to subtract 1 from the x-coordinate 
    # of the outer top-left corner of the game window for this to work.)
    window_topleft = (33, 271) 
    # window_bottomright = (673, 750)

    # util.print_mousepos_and_pixel() to get all values below, 
    # relative to top-left corner of window.
    sound = (313, 376)
    starting_menus = ((313, 210),
                      (313, 393),
                      (582, 452),
                      (313, 377))

    use_shrimp = (40, 338)
    use_rice = (94, 338)
    use_nori = (40, 396)
    use_roe = (94, 396)
    use_salmon = (40, 451)
    use_unagi = (94, 451)

    plates = (( 82, 210),
              (185, 210),
              (284, 210),
              (386, 210), 
              (489, 210),
              (586, 210))
    counter_pix = (238, 219, 169)

    phone = (585, 363)
    menu_toppings = (545, 273)
    buy_shrimp = (495, 225)
    buy_unagi = (575, 225)
    buy_nori = (495, 280)
    buy_roe = (575, 280)
    buy_salmon = (495, 335)
    exit_toppings = (590, 332)
    menu_rice = (545, 297)
    buy_rice = (547, 283)
    normal_delivery = (492, 295)
    mat = (212, 347)
    success_check_pos = (135, 231)
    menu_continue = (313, 377)
    submit_as_bot = (328, 262)
    bottom_continue = (321, 438)
    try_again = (216, 379)
    fail_menus = (menu_continue, submit_as_bot, 
                  bottom_continue, try_again)

    # Border color of the success and fail pop-ups.
    success_pix = (171, 245, 76)
    fail_pix = (255, 203, 45)

    # Pixel values of the toppings menu. 
    # on/off mean affordable/unaffordable.
    """
    shrimp_on = (255, 142, 95)
    shrimp_off = (127, 71, 47)
    unagi_on = (189, 98, 16)
    unagi_off = (94, 49, 8)
    nori_on = (66, 61, 22)
    nori_off = (33, 30, 11)
    roe_on = (255, 122, 0)
    roe_off = (127, 61, 0)
    salmon_on = (255, 142, 95)
    salmon_off = (127, 71, 47)
    rice_on = (255, 255, 255) 
    rice_off = (127, 127, 127)
    """
    on_off_threshold = 160
    on_off_nori = 50

    # GIMP again to get exact same box for each order balloon
    balloons_topleft = ((27, 61),
                       (128, 61),
                       (229, 61),
                       (330, 61),
                       (431, 61),
                       (532, 61))
    balloon_xlen = 62
    balloon_ylen = 15

    # Sum of the pixel values in the balloon for each type of order.
    # dish_menu order:
    # ['onigiri', 'caliroll', 'gunkan', 'salmonroll',
    #  'shrimproll', 'unagiroll', 'dragon', 'combo']
    order_pixsum = [575417, 626062, 501339, 526312,
                    424604, 419886, 514611, 236863]

    # Quit when levels_to_go reaches 0.
    levels_to_go = 7

    delivery_delay = 7 # seconds for order to arrive.

    # To check for and get rid of crap. 
    crap_x = 376
    crap_yrange = (469, 312) # Larger y first.
    crap_yrange_delta = -3
    crap_pix = (219, 140, 72)


class Util:

    def screen_grab(self, topleft, xlen, ylen):
        # topleft is relative to Glob.window_topleft, need to add it back.
        x0 = topleft[0] + Glob.window_topleft[0]
        y0 = topleft[1] + Glob.window_topleft[1]
        return autopy.bitmap.capture_screen( ((x0, y0), 
                                              (x0 + xlen, y0 + ylen)) )

    def get_pix(self, posxy):
    # Returns RGB value list for single pixel at posxy.
    # (It would have made more sense to use hex value if starting over.)
        return autopy.color.hex_to_rgb(
                autopy.screen.get_color(posxy[0] + Glob.window_topleft[0],
                                        posxy[1] + Glob.window_topleft[1]))

    def pix_sum(self, topleft, xlen, ylen):
        result = 0
        bmp = self.screen_grab(topleft, xlen, ylen)
        for x in xrange(xlen):
            for y in xrange(ylen):
                result += sum(autopy.color.hex_to_rgb(bmp.get_color(x, y)))
        return result

    def get_mouse_pos(self):
        pos = list(autopy.mouse.get_pos())
        for i in xrange(2):
            # Get position relative to topleft corner of game window.
            pos[i] -= Glob.window_topleft[i]
        return pos

    def move_mouse(self, posxy):
    # Have to correct game posxy to screen posxy.
        autopy.mouse.move(posxy[0] + Glob.window_topleft[0],
                                 posxy[1] + Glob.window_topleft[1])

    def clickon(self, posxy):
        self.move_mouse(posxy)
        time.sleep(0.05)
        autopy.mouse.click(autopy.mouse.LEFT_BUTTON)
        time.sleep(0.05)

    def print_mousepos_and_pixel(self):
        pos = self.get_mouse_pos()
        print 'Mouse is at:', pos 
        print 'Pixel at mouse pos is', self.get_pix(pos)    
        print 'Sum of pixel is', sum(self.get_pix(pos))
 
    def clear_tables(self):
        for plate in Glob.plates:
            for _ in xrange(3):
            # Check a few times, empty plates flash on and off.
                if sum(self.get_pix(plate)) != sum(Glob.counter_pix):
                    self.clickon(plate)
                    break
                time.sleep(0.0325)

    """
    def flatten(self, lista):
        if not hasattr(lista, '__contains__'):
            yield lista
        else:
            for sublist in lista:
                for elem in self.flatten(sublist):
                    yield elem
    """


class Dish(Util):
    def __init__(self, name, recipe):
        print 'Initializing Dish %s.' %name
        self.name = name
        self.recipe = recipe

    def fold_mat(self):
        start = time.time()
        self.clickon(Glob.mat)
        self.clean_crap()
        self.clear_tables()
        while time.time() - start < 1.0:
        # Mat takes about 1 sec to fold.
            time.sleep(0.1)

    def clean_crap(self):
    # Checks for and removes crap from dish loading area.
        for y in xrange(Glob.crap_yrange[0], 
                        Glob.crap_yrange[1], Glob.crap_yrange_delta):
            if sum(self.get_pix((Glob.crap_x, y))) == sum(Glob.crap_pix):
                print '\nSee poo!\n'
                self.clickon((Glob.crap_x, y))

    def make(self):
        for ingredient in self.recipe:
            ingredient.use()
        self.fold_mat()
        print 'Done making %s.' %self.name


class Ingredient(Util):
    def __init__(self, name, amount_incr, 
                 coord_use, coord_menu, coord_buy):
        print 'Initializing Ingredient %s.' %name
        self.name = name
        self.amount = amount_incr
        self.amount_incr = amount_incr
        self.coord_use = coord_use
        self.coord_menu = coord_menu
        self.coord_buy = coord_buy
        self.buy_locked = False

    def available(self):
        return self.amount

    def buy(self):
        self.clickon(Glob.phone)
        self.clickon(self.coord_menu)
        if self.affordable():
            self.clickon(self.coord_buy)
            self.clickon(Glob.normal_delivery)
            print 'Ordered %s.' %self.name
            self.parallel_thread(self.update_amount)
        else:
            # Works for rice too.
            self.clickon(Glob.exit_toppings)
            print 'Could not afford %s!' %self.name

    def update_amount(self):
        self.buy_locked = True
        time.sleep(Glob.delivery_delay)
        self.amount += self.amount_incr
        print 'Order arrived, now have %i of %s.' %(self.amount, self.name)
        self.buy_locked = False

    def parallel_thread(self, func):
        threading.Thread(target=func).start()

    def use(self):
        while self.amount < 1:
            print 'Out of %s! Waiting to get some.' %self.name
            if not self.buy_locked:
                self.buy()
            time.sleep(2)
        self.clickon(self.coord_use)
        self.amount -= 1
        # print 'Used 1 of %s.' %self.name
        if self.amount < 3 and not self.buy_locked:
            print 'Runnig low on %s:' %self.name,
            print '%i left. Trying to buy some now.' %self.amount
            self.buy()

    def affordable(self):
        pixR = self.get_pix(self.coord_buy)[0]
        # Have to make exception for nori, too dark.
        return pixR > Glob.on_off_threshold if self.name != 'nori' \
                                            else pixR > Glob.on_off_nori


class Seat(Util):
    def __init__(self, name, dish_menu, 
                 balloon_topleft, balloon_xlen, balloon_ylen):
        print 'Initializing Seat %i.' %name
        self.name = name
        self.dish_menu = dish_menu
        self.topleft = balloon_topleft
        self.xlen = balloon_xlen
        self.ylen = balloon_ylen
        self.curr_bloonpix = self.pix_sum(self.topleft, 
                                          self.xlen, self.ylen)
        self.prev_bloonpix = self.curr_bloonpix
        self.update_time = time.time()

    def update(self):
        self.prev_bloonpix = self.curr_bloonpix
        self.curr_bloonpix = self.pix_sum(self.topleft, 
                                          self.xlen, self.ylen)
        now = time.time()
        if self.curr_bloonpix != self.prev_bloonpix or  \
           now - self.update_time > 30: # Waiting too long. 
            if now - self.update_time > 30:
                print 'Table %i is idle. Checking.' %self.name
                self.check_success()
            self.place_order(self.order_index(self.curr_bloonpix))
            self.update_time = time.time()

    def order_index(self, bloonpix):
        if bloonpix in Glob.order_pixsum:
            return Glob.order_pixsum.index(bloonpix)

    def place_order(self, order_i):
        if order_i != None:
            print '\nTable %i\'s order is %s.' \
                                %(self.name, self.dish_menu[order_i].name)
            self.dish_menu[order_i].make()

    def check_success(self):
        pixR = self.get_pix(Glob.success_check_pos)[0]
        if  pixR == Glob.success_pix[0]:
            Glob.levels_to_go -= 1
            if Glob.levels_to_go == 0:
                print '\n________________MASTER CHEF________________\n'
                sys.exit(0)
            print '\nSuccess!! %i more days to go.' %Glob.levels_to_go
            time.sleep(0.5)
            start_level()
        elif pixR == Glob.fail_pix[0]:
            print '\nFailure... :('
            fail_level()

def reset():
    global seats
    print
    shrimp = Ingredient('shrimp', 5, Glob.use_shrimp, 
                        Glob.menu_toppings, Glob.buy_shrimp)
    rice = Ingredient('rice', 10, Glob.use_rice, 
                      Glob.menu_rice, Glob.buy_rice)
    nori = Ingredient('nori', 10, Glob.use_nori, 
                      Glob.menu_toppings, Glob.buy_nori)
    roe = Ingredient('roe', 10, Glob.use_roe, 
                     Glob.menu_toppings, Glob.buy_roe)
    salmon = Ingredient('salmon', 5, Glob.use_salmon, 
                        Glob.menu_toppings, Glob.buy_salmon)
    unagi = Ingredient('unagi', 5, Glob.use_unagi, 
                       Glob.menu_toppings, Glob.buy_unagi)
    print
    dish_menu = [Dish('onigiri', [rice, rice, nori]),
                 Dish('caliroll', [rice, nori, roe]),
                 Dish('gunkan', [rice, nori, roe, roe]),
                 Dish('salmonroll', [rice, nori, salmon, salmon]),
                 Dish('shrimproll', [rice, nori, shrimp, shrimp]),
                 Dish('unagiroll', [rice, nori, unagi, unagi]),
                 Dish('dragon', [rice, rice, nori, roe, unagi, unagi]),
                 Dish('combo', [rice, rice, nori, roe, 
                                unagi, salmon, shrimp])]
    print
    seats = []
    for i, topleft in enumerate(Glob.balloons_topleft):
        seats.append(Seat(i+1, dish_menu, topleft, 
                          Glob.balloon_xlen, Glob.balloon_ylen))

def start_level():
    for start_menu in Glob.starting_menus:
        util.clickon(start_menu)
    reset()

def fail_level():
    for fail_menu in Glob.fail_menus:
        if fail_menu == Glob.submit_as_bot:
            print 'Sleeping for 5'
            time.sleep(5)
        util.clickon(fail_menu)
        time.sleep(2)
    start_level()

def update_tables():
    util.clear_tables()
    for seat in seats:
        seat.update()

def kill_sound():
    util.clickon(Glob.sound)

def game_on():
    start_level()
    while True:
        update_tables()
        time.sleep(0.3)

def open_browser(url, loadtime=10):
    #webbrowser.open(url, 1, True)
    webbrowser.open_new(url)
    time.sleep(1)
    # os.system('xdotool key "Control_L+Super_L+Left"')
    autopy.key.tap(autopy.key.K_LEFT, 
                   autopy.key.MOD_CONTROL | autopy.key.MOD_META)
    time.sleep(loadtime)

def main(argv=[]):
    global util
    util = Util()
    if 'pix' in argv:
        util.print_mousepos_and_pixel()
    else:
        if 'browser' in argv:
            url = 'http://www.miniclip.com/games/sushi-go-round/en/'
            open_browser(url)
        if 'sound' not in argv:
            kill_sound()
        game_on()
  
if __name__ == "__main__":
    main(sys.argv)

