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

(deftag b [ignored] "0b")
(deftag h [ignored] "0x")

(setv hex-alphabet "1234567890abcdef")
(setv bit-alphabet "01")

(defmacro parse [buf type]
  `(-> (bitstring.ConstBitArray
         (+ ~type (.join "" (list-comp
                              (if (= (type x) str)
                                x
                                (chr x))
                              [x ~buf]))))
       (get (slice None None -1))
       (get (slice None wordsize))
       (get (slice None None -1))))

(defn from-hex-buf [hex-buf wordsize]
  (parse hex-buf #h()))

(defn from-hex-string [hex-string wordsize]
  (from-hex-buf (list-comp x [x hex-string]) wordsize))

(defn from-bit-buf [bit-buf wordsize]
  (parse bit-buf #b()))

(defn from-bit-string [bit-string wordsize]
  (from-bit-buf (list-comp x [x bit-string]) wordsize))
