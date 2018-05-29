(import [asciimatics.event [KeyboardEvent]])

(defmacro word-idx [coords]
  `(do
    (+
      (get ~coords 0)
      (* ui.words-in-line
        (get ~coords 1)))))

(defmacro keymap [&rest key-tuples]
  (dict-comp
    (first tup)
    (if (> (len tup) 2)
      `(fn []
        (when ~(get tup 2)
          (do
            (setv self.old-coords self.coords)
            ~(second tup))))
      `(fn []
        (setv self.old-coords self.coords)
        ~(second tup)))
    [tup key-tuples]))

(defclass BasicCursor [object]
  (defn --init-- [self ui]
    (setv self.ui ui)
    (setv self.coords (, 0 0))
    (setv self.old-coords self.coords)
    (setv self.cursor-at-word 0))
  (defn word-idx-in-view [self]
    (word-idx self.coords))
  (defn old-word-idx-in-view [self]
    (word-idx self.old-coords))
  (defn word-idx-in-file [self]
    (+ ui.starting-word (word-idx self.coords)))
  (defn handle-key-event [self k]
    (keymap
      [Screen.KEY-RIGHT
       (setv self.coords (, (+ (get self.coords 0) 1)
                            (get self.coords 1)))
       (< (.word-idx-in-file self) (- self.ui.total-words 1))]
      [Screen.KEY-LEFT
       (setv self.coords (, (- (get self.coords 0) 1)
                            (get self.coords 1)))
       (> (.word-idx-in-file self) 0)]
      [Screen.KEY-DOWN
       (setv self.coords (, (get self.coords 0)
                            (+ (get self.coords 1) 1)))
       (< (.word-idx-in-file self) (- self.ui.total-words self.ui.words-in-line))]
      [Screen.KEY-UP
       (setv self.coords , (get self.coords 0)
                            (- (get self.coords 1) 1))
       (> (.word-idx-in-file self) (- self.ui.words-in-line 1))])))