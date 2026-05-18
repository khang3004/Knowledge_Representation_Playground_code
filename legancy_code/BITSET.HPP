//  BitSet
//      2.10    25-Mar-1990
//      C++ 2.0
//
//      Defines a set of bits
//
//      Written by Scott Robert Ladd

#if !defined(_BitSet_HPP)
#define _BitSet_HPP

#include <stddef.h>
#include <string.h>

class BitSet
    {
    protected:
	unsigned long   Length;
	unsigned char far * Data;

    public:
    // constructors
    BitSet()
      {
      Length = 0L;
      Data   = NULL;
      }

    BitSet(unsigned long size);

    BitSet(BitSet & bs);

    // destructor
    ~BitSet(void);

    // ŸÞnh l«i Size
    void InitSize(unsigned long size);

    // assignment operator
    void operator = (BitSet & bs);

    // Get number of bits in set
    unsigned long Size()
      {
      return Length;
      }

    // operation methods
    void Include(unsigned long bit)
       {
       if (bit < Length)
	 Data[bit / 8] |= (unsigned char)(1 << (bit & 7));
       }

    void Exclude(unsigned long bit)
       {
       if (bit < Length)
	 Data[bit / 8] &= ~(unsigned char)(1 << (bit & 7));
       }

    // turn all bits in set on
    void AllOn()
       {
       _fmemset(Data,'\xFF',(Length + 7) / 8);
       }

   // turn all bits in set off
   void AllOff()
      {
      _fmemset(Data,'\x00',(Length + 7) / 8);
      }

   // union operators
   BitSet operator | (BitSet & bs);
   BitSet operator |= (BitSet & bs);

   // synonyms for union operators
   BitSet operator +  (BitSet & bs);
   BitSet operator += (BitSet & bs);

   // intersection operators
   BitSet operator &  (BitSet & bs);
   BitSet operator &= (BitSet & bs);

   // difference operators
   BitSet operator -  (BitSet & bs);
   BitSet operator -= (BitSet & bs);

   // complement operator
   BitSet operator ~ ();

   // comparison operator
   int operator == (BitSet & bs);
   int operator != (BitSet & bs);

   // value retrieval method
   int operator [] (unsigned long bit)
      {
      if (bit < Length)
	return (Data[bit / 8] & (1 << (bit & 7)));
      else
	return 0;
      }
    };  // class BitSet

#endif
