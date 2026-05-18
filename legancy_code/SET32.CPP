#include "SET32.HPP"

#include <stdio.h>

//============== cªc h§m cña t¾p set32 ==================

//-----------------------------------
int Bit (int i, set32 A)
{
  return((A>>i) & 1L);
}

//-----------------------------------
void Include (int i, set32 far & A)
{
  if (0<=i && i<32)
     A |= (1L<<i);
}

//-----------------------------------
void Exclude (int i, set32 far & A)
{
  if (0<=i && i<32)
     A &= ~(1L<<i);
}

//-----------------------------------
void Empty(set32 far & A)
{
  A = (set32) 0x0;
}

//-----------------------------------
void Full(set32 far & A)
{
  A = 0xFFFFFFFF;
}

//-----------------------------------
set32 Complement(set32 A)
{
  set32 result;
  result = ~A;
  return (result);
}

//-----------------------------------
set32 Intersect(set32 A,set32 B)
{
  set32 result;
  result = A & B;
  return (result);
}

//-----------------------------------
set32 Union(set32 A,set32 B)
{
  set32 result;
  result = A | B;
  return (result);
}

//-----------------------------------
set32 Minus(set32 A,set32 B)
{
  set32 result;
  result = A & ~B;
  return (result);
}
//-----------------------------------
int IsEmpty(set32 A)
{
  return ((A==0x00000000)? 1:0);
}
//-----------------------------------
int Equal(set32 A,set32 B)
{
  return (A==B);
}
//-----------------------------------
int In(set32 A,set32 B)
// kiÓm tra sù bao h§m. nÕu A bao h§m trong B th× return 1
{
  if ( Equal(Intersect(A,B),A) )
    return (1);
  return 0;
}
//-----------------------------------
int Card(set32 A)
// ¦Õm sè ph¶n tö cña t¾p hîp
{
  int count = 0;
  int i;
  for (i=0; i<32; i++)
    if (Bit(i,A))
      count += 1;
  return count;
}
//--------------------------------------------------
void OutSet32(set32 A)
{
  int i;
  for (i=0; i<32; i++)
    putchar(Bit(i,A)+'0');
  putchar('\n');
}

//============== cªc h§m cña t¾p set32_64 ==================

//--------------------------------------------------
int BitN (int k, set32N far A)
{
  int i,j;
  i = k/32;  j = k % 32;
  return (Bit(j,A[i]));
}
//--------------------------------------------------
void IncludeN(int k, set32N far A)
{
  int i,j;
  i = k/32;  j = k % 32;
  Include(j,A[i]);
}
//--------------------------------------------------
void ExcludeN (int k, set32N far A)
{
  int i,j;
  i = k/32;  j = k % 32;
  Exclude(j,A[i]);
}
//--------------------------------------------------
void EmptyN(set32N far A)
{
  int i;
  for (i=0; i<NoSet32; i++)
    Empty(A[i]);
}
//--------------------------------------------------
void FullN(set32N far A)
{
  int i;
  for (i=0; i<NoSet32; i++)
    Full(A[i]);
}
//--------------------------------------------------
void ComplementN(set32N A,set32N C)
{
  int i;
  for (i=0; i<NoSet32; i++)
    C[i] = Complement(A[i]);
}
//--------------------------------------------------
void IntersectN(set32N A,set32N B,set32N C)
{
  int i;
  for (i=0; i<NoSet32; i++)
    C[i] = Intersect(A[i],B[i]);
}
//--------------------------------------------------
void UnionN(set32N A,set32N B,set32N C)
{
  int i;
  for (i=0; i<NoSet32; i++)
    C[i] = Union(A[i],B[i]);
}
//--------------------------------------------------
void MinusN(set32N A,set32N B,set32N C)
{
  int i;
  for (i=0; i<NoSet32; i++)
    C[i] = Minus(A[i],B[i]);
}
//--------------------------------------------------
int IsEmptyN(set32N A)
{
  int i;
  for (i=0; i<NoSet32; i++)
    if (!IsEmpty(A[i]))  return 0;
  return 1;
}
//--------------------------------------------------
int EqualN(set32N A,set32N B)
// kiÓm tra sù b¬ng nhau
{
  int i;
  for (i=0; i<NoSet32; i++)
    if (!Equal(A[i],B[i]))
      return 0;
  return 1;
}
//--------------------------------------------------
int InN(set32N A,set32N B)
// kiÓm tra sù bao h§m
{
  int i;
  for (i=0; i<NoSet32; i++)
    if (!In(A[i],B[i]))
      return 0;
  return 1;
}
//--------------------------------------------------
int CardN(set32N A)
// ¦Õm sè ph¶n tö cña t¾p hîp
{
  int i, count=0;
  for (i=0; i<NoSet32; i++)
    count += Card(A[i]);
  return (count);
}
//--------------------------------------------------
void AssignSet32N(set32N dest, set32N src)
// lÖnh gªn t¾p set32N
{
  int i;
  for (i=0; i<NoSet32; i++)
    dest[i]=src[i];
}
