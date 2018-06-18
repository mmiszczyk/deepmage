;;;;;;;;;;;;;;;;;;;;;;;
; This file is a part ;
;   of the deepmage   ;
;  project, released  ;
; under the GNU GPL 3 ;
;      license        ;
;  (see the COPYING   ;
;  file for details)  ;
;;;;;;;;;;;;;;;;;;;;;;;

(import [asciimatics.event [KeyboardEvent]])
(import [asciimatics.screen [Screen]])
(import bitstring)

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

(defmacro basic-cursor-print [coords view-indexing-method attr]
  `(.print-at self.ui.screen
    (self.ui.representation (get self.ui.view (~view-indexing-method)))
    (* (get ~coords 0) (+ self.ui.chars-per-word 1))
    (+ (get ~coords 1) 1)
    :attr ~attr))

(defclass BasicCursor [object]
  (defn --init-- [self ui &optional coords]
    (setv self.ui ui)
    (setv self.coords (if coords coords (, 0 0)))
    (setv self.old-coords self.coords)
    (setv self.cursor-at-word 0)
    (setv self.alphabet "1234567890abcdef")
    (setv self.write-buffer [])
    (setv self.keys
      (keymap                   ; we execute a function corresponding to a key
          [Screen.*key-right*   ; if a condition is satisfied
           (setv self.coords (, (+ (get self.coords 0) 1)
                                (get self.coords 1)))
           (< (.word-idx-in-file self) (- self.ui.total-words 1))]
          [Screen.*key-left*
           (setv self.coords (, (- (get self.coords 0) 1)
                                (get self.coords 1)))
           (> (.word-idx-in-file self) 0)]
          [Screen.*key-down*
           (setv self.coords (, (get self.coords 0)
                                (+ (get self.coords 1) 1)))
           (< (.word-idx-in-file self) (- self.ui.total-words self.ui.words-in-line))]
          [Screen.*key-up*
           (setv self.coords (, (get self.coords 0)
                                (- (get self.coords 1) 1)))
           (> (.word-idx-in-file self) (- self.ui.words-in-line 1))]
           [Screen.*key-home*
            (setv self.coords (, 0
                                 (get self.coords 1)))]
           [Screen.*key-end*
            (setv self.coords (, (- self.ui.words-in-line 1)
                                 (get self.coords 1)))]
           [Screen.*key-page-up*
            (do
              (setv self.ui.starting-word (- self.ui.starting-word self.ui.words-in-view))
              (setv self.ui.view-changed True))]
           [Screen.*key-page-down*
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
    (setv self.write-buffer [])
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
    (defn highlight [self]
      (try
        (do
          (basic-cursor-print self.old-coords self.old-word-idx-in-view Screen.*a-normal*)
          (basic-cursor-print self.coords     self.word-idx-in-view     Screen.*a-reverse*))
        (except [IndexError] None))
      (setv self.old-coords None))
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
        (+ (* " " self.ui.screen.width))))
  (defn write-at-cursor [self char]
    (unless (in (chr char) self.alphabet) (raise (ValueError "Not a hex digit")))
    (.append self.write-buffer char)
    (when (= (len self.write-buffer) self.ui.chars-per-word)
      (assoc self.ui.reader (.word-idx-in-file self)
        (-> (bitstring.ConstBitArray
              (+ "0x" (.join "" (list-comp (chr x) [x self.write-buffer]))))
            (get (slice None None -1))
            (get (slice None (.get-wordsize self.ui.reader)))
            (get (slice None None -1))))
      (setv self.ui.view-changed True)
      (.handle-key-event self Screen.*key-right*))))

(defmacro bit-cursor-print [coords bit-idx view-indexing-method attr]
  `(.print-at self.ui.screen
    (get (self.ui.representation (get self.ui.view (~view-indexing-method))) ~bit-idx)
    (+ (* (get ~coords 0) (+ self.ui.chars-per-word 1)) ~bit-idx)
    (+ (get ~coords 1) 1)
    :attr ~attr))

(defclass BitCursor [BasicCursor]
  (defn --init-- [self ui &optional coords]
    (.--init-- (super BitCursor self) ui (when coords coords))
    (setv self.alphabet "01")
    (setv self.bit-idx 0)
    (setv self.old-bit-idx 0)
    (.update self.keys (keymap
      [Screen.*key-right*
       (do
         (setv self.old-bit-idx self.bit-idx)
         (setv self.bit-idx (+ self.bit-idx 1))
         (when (>= self.bit-idx (.get-wordsize self.ui.reader))
           (do
             (setv self.bit-idx 0)
             (if (<  (.word-idx-in-file self) (- self.ui.total-words 1))
               (setv self.coords (, (+ (get self.coords 0) 1)
                                    (get self.coords 1)))
               (setv self.bit-idx (- (.get-wordsize self.ui.reader) 1))))))]
      [Screen.*key-left*
       (do
         (setv self.old-bit-idx self.bit-idx)
         (setv self.bit-idx (- self.bit-idx 1))
         (when (< self.bit-idx 0)
           (do
             (setv self.bit-idx (- (.get-wordsize self.ui.reader) 1))
             (if (> (.word-idx-in-file self) 0)
               (setv self.coords (, (- (get self.coords 0) 1)
                                  (get self.coords 1)))
               (setv self.bit-idx 0)))))])))
  (defn get-human-readable-position-data [self]
    (-> "{}[{}]/{}[{}] {}"
        (.format
          (+ (.word-idx-in-file self) 1)
          (+ self.bit-idx 1)
          self.ui.total-words
          (.get-wordsize self.ui.reader)
          self.coords)
        (+ (* " " self.ui.screen.width))))
  (defn highlight [self]
      (try
        (do
          (if (or (= self.coords self.old-coords) (= self.old-coords None))
            (bit-cursor-print self.old-coords self.old-bit-idx self.old-word-idx-in-view Screen.*a-normal*)
            (basic-cursor-print self.old-coords self.old-word-idx-in-view Screen.*a-normal*))
          (bit-cursor-print self.coords self.bit-idx self.word-idx-in-view Screen.*a-reverse*))
        (except [IndexError] None))
      (setv self.old-coords None)
      (setv self.old-bit-idx 0))
  (defn write-at-cursor [self char]
    (unless (in (chr char) self.alphabet) (raise (ValueError "Not a binary digit")))
    (setv word (get self.ui.reader (.word-idx-in-file self)))
    (assoc word self.bit-idx (if (= (chr char) "1") True False))
    (assoc self.ui.reader (.word-idx-in-file self) word)
    (setv self.ui.view-changed True)
    (.handle-key-event self Screen.*key-right*)))