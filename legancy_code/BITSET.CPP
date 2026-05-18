//  BitSet
//      2.10    25-Mar-1990
//      C++ 2.0
//
//      Defines a set of bits
//
//      Written by Scott Robert Ladd

#include "BitSet.hpp"

#include <stddef.h>
#include <string.h>

// constructors
BitSet::BitSet(unsigned long size)
    {
    unsigned long alloc;

    Length = size;

    alloc = (size + 7) / 8;

    Data = new unsigned char[(unsigned int)alloc];

    _fmemset(Data,'\x00',(unsigned int)alloc);
    }

BitSet::BitSet(BitSet & bs)
    {
    unsigned long alloc;

    Length = bs.Length;

    alloc = (bs.Length + 7) / 8;

    Data = new unsigned char[(unsigned int)alloc];

    _fmemcpy(Data,bs.Data,(unsigned int)alloc);
    }

// destructor
BitSet::~BitSet(void)
    {
    if (Data != NULL)
	delete Data;
    }

//---------------------------------------------
void BitSet::InitSize(unsigned long size)
{
  BitSet bs(size);
  *this |= bs;
}

// assignment operator
void BitSet::operator = (BitSet & bs)
    {
    unsigned long alloc;

    if (Length != bs.Length)
	{
	Length = bs.Length;

	alloc = (bs.Length + 7) / 8;

	if (Data != NULL)
	    delete Data;

	Data = new unsigned char[(unsigned int)alloc];

	_fmemcpy(Data,bs.Data,(unsigned int)alloc);
	}
    else
	_fmemcpy(Data,bs.Data,(unsigned int)((Length + 7) / 8));
    }

// union operators
BitSet BitSet::operator | (BitSet & bs)
    {
    BitSet result;
    unsigned long bit;

    if (Length < bs.Length)
	{
	result = bs;
	for (bit = 0; bit < Length; ++bit)
	    if ((*this)[bit])
		result.Include(bit);
	}
    else
	{
	result = *this;
	for (bit = 0; bit < bs.Length; ++bit)
	    if (bs[bit])
		result.Include(bit);
	}
    return result;
    }

BitSet BitSet::operator |= (BitSet & bs)
    {
    *this = *this | bs;
    return *this;
    }

// synonyms for union operators
BitSet BitSet::operator + (BitSet & bs)
    {
    BitSet result = *this | bs;
    return result;
    }

BitSet BitSet::operator += (BitSet & bs)
    {
    BitSet result = (*this |= bs);
    return result;
    }

// intersection operators
BitSet BitSet::operator & (BitSet & bs)
    {
    BitSet result;
    unsigned long max;
    if (Length > bs.Length)
	{
	result = BitSet(Length);
	max    = bs.Length;
	}
    else
	{
	result = BitSet(bs.Length);
	max    = Length;
	}

    for (unsigned long bit = 0; bit < max; ++bit)
	if ((*this)[bit] & bs[bit])
	    result.Include(bit);
    return result;
    }

BitSet BitSet::operator &= (BitSet & bs)
    {
    *this = *this & bs;
    return *this;
    }

// difference operators
BitSet BitSet::operator - (BitSet & bs)
    {
    BitSet result = *this;
    unsigned long stop = (Length < bs.Length) ? Length : bs.Length;
    for (unsigned long bit = 0; bit < stop; ++bit)
	if (bs[bit])
	    result.Exclude(bit);
    return result;
    }

BitSet BitSet::operator -= (BitSet & bs)
    {
    *this = *this - bs;
    return *this;
    }

// complement operator
BitSet BitSet::operator ~ ()
    {
    BitSet result(Length);
    for (unsigned long bit = 0; bit < Length; ++bit)
	if ((*this)[bit])
	    result.Exclude(bit);
	else
	    result.Include(bit);
    return result;
    }

// comparison operators
int BitSet::operator == (BitSet & bs)
    {
    if (Length != bs.Length)
	return 0;
    for (unsigned long bit = 0; bit < Length; ++bit)
	if ((*this)[bit] != bs[bit])
	    return 0;
    return 1;
    }

int BitSet::operator != (BitSet & bs)
    {
    if (Length != bs.Length)
	return 1;
    unsigned long bit = 0;
    while (bit < Length)
	if ((*this)[bit] == bs[bit])
	    ++bit;
	else
	    return 1;
    return 0;
    }
