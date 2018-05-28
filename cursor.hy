(import [asciimatics.event [KeyboardEvent]])

(defmacro word-idx [coords]
  `(do
    (+
      (get ~coords 0)
      (* ui.words-in-line
        (get ~coords 1)))))

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
    (+ ui.starting-word (word-idx self.coords))))