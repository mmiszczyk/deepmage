(import [asciimatics.event [KeyboardEvent]])
(import [asciimatics.screen [Screen]])

(defmacro word-idx [coords]
  `(do
    (+
      (get ~coords 0)
      (* self.ui.words-in-line
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
    (setv self.cursor-at-word 0)
    (setv self.keys
      (keymap               ; we execute a function corresponding to a key
          [Screen.KEY-RIGHT   ; if a condition is satisfied
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
           (setv self.coords (, (get self.coords 0)
                                (- (get self.coords 1) 1)))
           (> (.word-idx-in-file self) (- self.ui.words-in-line 1))]
           [Screen.KEY-HOME
            (setv self.coords (, 0
                                 (get self.coords 1)))]
           [Screen.KEY-END
            (setv self.coords (, (- self.ui.words-in-line 1)
                                 (get self.coords 1)))]
           [Screen.KEY-PAGE-UP
            (do
              (setv self.ui.starting-word (- self.ui.starting-word self.ui.words-in-view))
              (setv self.ui.view-changed True))]
           [Screen.KEY-PAGE-DOWN
            (do
              (setv self.ui.starting-word (+ self.ui.starting-word self.ui.words-in-view))
              (setv self.ui.view-changed True))
            (< self.ui.starting-word (- self.ui.total-words self.ui.words-in-view))])))
  (defn word-idx-in-view [self]
    (word-idx self.coords))
  (defn old-word-idx-in-view [self]
    (word-idx self.old-coords))
  (defn word-idx-in-file [self]
    (+ self.ui.starting-word (word-idx self.coords)))
  (defn cursor-moved [self]
    (setv old-start self.ui.starting-word)
    (cond
      [(>= (get self.coords 0) self.ui.words-in-line)  ; checking the line boundaries
       (setv self.coords (, 0                          ; and handling edge cases
                            (+ (get self.coords 1) 1)))]
      [(< (get self.coords 0) 0)
        (setv self.coords (, (- self.ui.words-in-line 1)
                             (- (get self.coords 1) 1)))])
    (cond
      [(>= (get self.coords 1) self.ui.lines)
       (do (setv self.ui.starting-word (+ self.ui.starting-word self.ui.words-in-line))
           (setv self.coords (, (get self.coords 0)
                                (- self.ui.lines 1))))]
      [(< (get self.coords 1) 0)
       (do (setv self.ui.starting-word
             (if
               (> self.ui.starting-word 0)
               (- self.ui.starting-word self.ui.words-in-line)
               0))
           (setv self.coords (, (get self.coords 0)
                                0)))])
    (when (>  (.word-idx-in-file self) self.ui.total-words)
      (setv self.coords (, (- (% self.ui.total-words self.ui.words-in-line) 1)
                           (// (- self.ui.total-words self.ui.starting-word 1) self.ui.words-in-line))))
    (setv self.ui.starting-word
      (max 0
        (min self.ui.starting-word
          (+
            (- self.ui.total-words self.ui.words-in-line)
            (% self.ui.starting-word self.ui.words-in-line)))))
    (unless (= old-start self.ui.starting-word) (setv self.ui.view-changed True)))
  (defn handle-key-event [self k]
    (try
      ((get self.keys k))
      (except [KeyError] (return)))  ; if no keypress was recognized, we return early
      (.cursor-moved self))
  (defn get-human-readable-position-data [self]
    (-> "{}/{} {}"
        (.format
          (+ (.word-idx-in-file self) 1)
          self.ui.total-words
          self.coords)
        (+
          (* " " self.ui.screen.width)))))