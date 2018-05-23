(import bitstring)

(require [hy.extra.anaphoric [ap-each-while ap-each]])

(defclass Chunk [object]
  (defn --init-- [self file offset size]
    (setv self.file file)
    (setv self.offset offset)
    (setv self.size size)
    (setv self.loaded False)
    (setv self.modified False)
    (setv self.contents None))
  (defn load [self]
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
    (get self.contents key))
  (defn --setitem-- [self key value]
    (unless self.loaded (.load self))
    (unless (= value (get self.contents key))
      (do
        (assoc self.contents key value)
        (setv self.modified True)))))

; do something with every bit in a word:
; current bit can be accessed with the 'bit' symbol
; and modified with the '(set-bit value)' macro
(defmacro for-bit-in-word [key form]
  `(do
    (setv i 0)
    (setv unique (set))
    (setv end (get (.get_word_boundaries self ~key) 1))
    (ap-each-while
      (map (fn [x] (.get_bit_coords self x)) (range self.wordsize))
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
                         [i (range self.filesize)])))
    (setv self.wordsize 8))
  (defn set_wordsize [self wordsize]
    (when (< wordsize 1) (raise (ValueError "wordsize cannot be smaller than 1!")))
    (setv self.wordsize wordsize))
  (defn get_wordsize [self] self.wordsize)
  ; returns a tuple which contains a chunk index and index of bit in chunk
  (defn get_bit_coords [self bit_idx]
    (if (> bit_idx (+ 7 (* 8 self.filesize)))
      (+ 7 (* 8 self.filesize))
      (, (// bit_idx self.chunksize)
         (% bit_idx self.chunksize))))
  ; returns coordinates (see: get_bit_coords) of word's first and last bit
  (defn get_word_boundaries [self word_idx]
    (, (.get_bit_coords self (* word_idx self.wordsize))
       (.get_bit_coords self (- (* (+ word_idx 1) self.wordsize) 1))))
  (defn --getitem-- [self word_number]
    (setv ret [])
    (for-bit-in-word word_number
      (.append ret bit))
    ret)
  (defn --setitem-- [self word_number value]
    (for-bit-in-word word_number
      (set-bit (get value i))))
  (defn save [self] (ap-each self.chunks (when it.modified (.save it)))))