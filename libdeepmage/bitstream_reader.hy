;;;;;;;;;;;;;;;;;;;;;;;
; This file is a part ;
;   of the deepmage   ;
;  project, released  ;
; under the GNU GPL 3 ;
;      license        ;
;  (see the COPYING   ;
;  file for details)  ;
;;;;;;;;;;;;;;;;;;;;;;;

(import bitstring)
(import math)

(require [hy.extra.anaphoric [ap-each-while ap-each]])

(defclass Chunk [object]
  (defn --init-- [self file offset size]
    (setv self.file file)
    (setv self.offset offset)
    (setv self.size size)
    (setv self.loaded False)
    (setv self.modified False)
    (setv self.in-view False)
    (setv self.contents None))
  (defn load [self]
    (when self.loaded (return))
    (.seek self.file self.offset)
    (setv self.contents (bitstring.BitStream (.read self.file self.size)))
    (setv self.loaded True)
    (setv self.modified False))
  (defn unload [self]
    (setv self.loaded False)
    (setv self.contents None))
  (defn save [self]
    (.seek self.file self.offset)
    (.write self.file self.contents.bytes)
    (setv self.modified False))
  (defn --getitem-- [self key]
    (unless self.loaded (.load self))
    (try
      (get self.contents key)
      (except [IndexError] None)))
  (defn --setitem-- [self key value]
    (unless self.loaded (.load self))
    (unless (= value (get self.contents key))
      (do
        (assoc self.contents key value)
        (setv self.modified True)))))

(defmacro for-chunk-in-view [form]
  `(do
    (unless self.chunks
      (setv begin (->
                    (.get-word-boundaries self.reader self.begin-idx)
                    (get 0)
                    (get 0)))
      (setv end   (->
                      (.get-word-boundaries self.reader
                        (+ self.begin-idx
                          (len self.words)))
                      (get 1)
                      (get 0)
                      (+ 1)))
      (for [i (range begin end)]
        (when (< i (len self.reader.chunks))
          (.append self.chunks (get self.reader.chunks i)))))
      (for [chunk self.chunks] ~form)))

(defclass View [object]
  (defn --init-- [self reader begin-idx words]
    (setv self.reader reader)
    (setv self.begin-idx begin-idx)
    (setv self.words words)
    (setv self.chunks [])
    (for-chunk-in-view (setv chunk.in-view True)))
  (defn bounds-check [self key]
    (unless (< key (len self.words))
      (raise (IndexError
        (.format "Trying to access element {0} of a {1}-element view" key (len self.words))))))
  (defn --getitem-- [self key]
    (.bounds-check self key)
    (get self.reader (+ self.begin-idx key)))
  (defn --setitem-- [self key value]
    (.bounds-check self key)
    (assoc self.reader (+ self.begin-idx key) value))
  (defn unload-view [self]
    (for-chunk-in-view (setv chunk.in-view False))))

(defmacro for-each-chunk [form]
  `(ap-each self.chunks ~form))

; do something with every bit in a word:
; current bit can be accessed with the 'bit' symbol
; and modified with the '(set-bit value)' macro
(defmacro for-bit-in-word [key form]
  `(do
    (setv i 0)
    (setv unique (set))
    (setv startbit (* self.wordsize ~key))
    (setv end (get (.get-word-boundaries self ~key) 1))
    (ap-each-while
      (map (fn [x] (.get-bit-coords self x)) (range startbit (+ startbit self.wordsize )))
      (and (<= it end) (not (in it unique)))
      (do
        (setv bit (get self.chunks (get it 0) (get it 1)))
        ~form
        (setv i (inc i))
        (.add unique it)))))

; this is a convenience macro ONLY for use inside the for-bit-in-word macro
(defmacro set-bit [value]
  `(assoc
    (get self.chunks
      (get it 0))
    (get it 1)
    ~value))

(defclass FileReader [object]
  (defn --init-- [self file chunksize]
    (setv self.file file)
    (setv self.filesize (do
                         (.seek file 0 2)
                         (.tell file)))
    (setv self.chunksize chunksize)
    (setv self.chunks (do
                       (.seek file 0)
                       (list-comp
                         (Chunk file
                           (* i chunksize)
                           chunksize)
                         [i (range (int (math.ceil (/ self.filesize chunksize))))])))
    (setv self.wordsize 8)
    (setv self.view None))
  (defn set-wordsize [self wordsize]
    (when (< wordsize 1) (raise (ValueError "wordsize cannot be smaller than 1!")))
    (setv self.wordsize wordsize))
  (defn get-wordsize [self] self.wordsize)
  (defn get-wordcount [self]
    (// (* 8 self.filesize) self.wordsize))
  (defn stop-at-last-bit [self bit-idx]
    (if (> bit-idx (+ 7 (* 8 self.filesize)))
      (+ 7 (* 8 self.filesize))
      bit-idx))
  ; returns a tuple which contains a chunk index and index of bit in chunk
  (defn get-bit-coords [self bit-idx]
    (->
      (map self.stop-at-last-bit
        (, (// bit-idx (* 8 self.chunksize))
           (% bit-idx (* 8 self.chunksize))))
      (tuple)))
  ; returns coordinates (see: get-bit-coords) of word's first and last bit
  (defn get-word-boundaries [self word-idx]
    (, (.get-bit-coords self (* word-idx self.wordsize))
       (.get-bit-coords self (- (* (+ word-idx 1) self.wordsize) 1))))
  (defn --getitem-- [self word-number]
    (if (<= word-number (.get-wordcount self))
      (do
        (setv ret [])
        (for-bit-in-word word-number
          (unless (= bit None) (.append ret bit)))
        ret)
        []))
  (defn --setitem-- [self word-number value]
    (for-bit-in-word word-number
      (set-bit (get value i))))
  (defn save [self]  (for-each-chunk
                       (when
                         it.modified
                         (.save it))))
  (defn purge [self] (for-each-chunk
                       (unless
                         (or it.modified it.in-view (not it.loaded))
                         (.unload it))))
  (defn get-view [self first-word-idx number-of-words]
    (when self.view (.unload-view self.view))
    (setv self.view (View
      self
      first-word-idx
      (list-comp
        (get self word-number)
        [word-number
          (range first-word-idx
            (+ first-word-idx number-of-words))])))
    (.purge self)
    self.view))