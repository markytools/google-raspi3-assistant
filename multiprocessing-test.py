#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import random
from multiprocessing import Queue, Manager

myglobal = 0

#~ class MyClass(object):
    #~ def __init__(self, word):
        #~ self.word = word
        
class MultiProcessQueue(multiprocessing.Queue):
    def __init__(self, maxsize=20):
        super(MultiProcessQueue, self).__init__(maxsize)

    def clear(self):
        '''Clears all items from the queue. '''

        with self.mutex:
          unfinished = self.unfinished_tasks - len(self.queue)
          if unfinished <= 0:
            if unfinished < 0:
              raise ValueError('task_done() called too many times')
            self.all_tasks_done.notify_all()
          self.unfinished_tasks = unfinished
          self.queue.clear()
          self.not_full.notify_all()
          
    def __getstate__(self):
        return super(InputJobQueue, self).__getstate__() + (self._max_size,)

    def __setstate__(self, state):
        super(InputJobQueue, self).__setstate__(state[:-1])
        self._max_size = state[-1]

#~ def af(q, myclass):
    #~ global myglobal
    #~ while True:
        #~ print("Hello" + myclass.word)
#~ 
#~ def bf(q, myclass):
    #~ global myglobal
    #~ while True:
        #~ print("Hello2" + myclass.word)

def main():
    a = MultiProcessQueue()  
    #~ myclass1 = MyClass("haha")
    #~ myclass2 = MyClass("i don't know'")
    #~ p = Process(target=af, args=(a, myclass1,))
    #~ c = Process(target=bf, args=(a, myclass2,))
    #~ p.start()
    #~ c.start()
    #~ p.join()
    #~ c.join()


if __name__ == "__main__":
    main()
