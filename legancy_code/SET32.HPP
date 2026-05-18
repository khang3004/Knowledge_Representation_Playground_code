#if !defined(SET_32)

#define SET_32

typedef unsigned long set32;

// ========================================================

int Bit (int i, set32 A);

void Include (int i, set32 far & A);
void Exclude (int i, set32 far & A);

void Empty(set32 far & A);
void Full(set32 far & A);

set32 Complement(set32 A);

set32 Intersect(set32 A,set32 B);
set32 Union(set32 A,set32 B);
set32 Minus(set32 A,set32 B);
// return A\B

int IsEmpty(set32 A);
int Equal(set32 A,set32 B);
// kiÓm tra sù b¬ng nhau, return 1 nÕu b¬ng, return 0 nÕu khªc
int In(set32 A,set32 B);
// kiÓm tra sù bao h§m. nÕu A bao h§m trong B th× return 1
int Card(set32 A);
// ¦Õm sè ph¶n tö cña t¾p hîp

void OutSet32(set32 A);
// in ra cªc bit cña set32

// ======================== SET32_64 =========================
// t¾p hîp kÕt hîp (héi rêi nhau) cña tèi ¦a 64 t¾p hîp 32 bit

#define NoSet32 64
typedef  set32 set32N[NoSet32];

int BitN (int k, set32N far A);

void IncludeN(int k, set32N far A);
void ExcludeN (int k, set32N far A);

void EmptyN(set32N far A);
void FullN(set32N far A);

void ComplementN(set32N A,set32N C);

void IntersectN(set32N A,set32N B,set32N C);
void UnionN(set32N A,set32N B,set32N C);
void MinusN(set32N A,set32N B,set32N C);
// C = A \ B

int IsEmptyN(set32N A);
int EqualN(set32N A,set32N B);
// kiÓm tra sù b¬ng nhau
int InN(set32N A,set32N B);
// kiÓm tra sù bao h§m cña A trong B
int CardN(set32N A);
// ¦Õm sè ph¶n tö cña t¾p hîp

void AssignSet32N(set32N dest, set32N src);
// lÖnh gªn t¾p set32N


#endif
