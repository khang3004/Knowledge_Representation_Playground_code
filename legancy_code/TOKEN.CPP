#include "TOKEN.HPP"

#include <string.h>
#include <alloc.h>
#include <math.h>

//====================== cªc biÕn ===================

// Cªc t¢n h§m. H§m cã t¢n h§m kÕ l§ "!Invert" th× kh£ng cã h§m ng¥îc.
TOKEN Fnames[] = {"sqr","sqrt","ln","exp",
		  "sin","arcsin","cos","arccos"
		  };
#define N_Fnames sizeof(Fnames)/sizeof(TOKEN)
// Cªc t¢n toªn tö
TOKEN Onames[] = {"+","-","*","/","^","="};
#define N_Onames sizeof(Onames)/sizeof(TOKEN)
// cªc ký tù kh£ng thuéc Token1
char NotInToken1[] = { ' ','\\','%','$','{','}','(',')',':',
	'+','-','*','/','^',',','.',';','='
	};
#define N_NotInToken1 sizeof(NotInToken1)/sizeof(char)

//====================== hÕt cªc biÕn ===================


//------------------------------------------------
int IsDigit(char c)
{
  if ('0'<=c && c<='9') return(1);
  return(0);
}
//------------------------------------------------
int IsLetter(char c)
{
  if ('a'<=c && c<='z') return(1);
  if ('A'<=c && c<='Z') return(1);
  return(0);
}
//------------------------------------------------
int IsOperator(char far *pc)
{
  int i;
  for (i=0; i<N_Onames; i++)
    if (_fstrcmp(pc,Onames[i])==0)
      return(1);
  return(0);
}
//------------------------------------------------
int IsFuncName(char far *pc)
{
  int i;
  for (i=0; i<N_Fnames; i++)
    if (_fstrcmp(pc,Fnames[i])==0)
      return(1);
  return(0);
}
//------------------------------------------------
int InvertFuncName(char far *fn, char far * Invfn)
// T×m t¢n h§m ng¥îc, nÕu cã th× return 1, ng¥îc l«i return 0.
{
  int i;
  for (i=0; i<N_Fnames; i++)
    if (_fstrcmp(fn,Fnames[i])==0)
      {
      if (i%2==0 && _fstrcmp(Fnames[i+1],"!Invert")!=0)
	{ _fstrcpy(Invfn,Fnames[i+1]);  return 1;
	}
      if (i%2==1)
	{ _fstrcpy(Invfn,Fnames[i-1]);  return 1;
	}
      }
  return 0;
}
//------------------------------------------------
int GetStrChar(char far *des,char far *src, int &pos,char c)
{
  char far *p, *q;

  if (pos<0 || pos>=_fstrlen(src))  return 0; // kh£ng l½y ¦¥îc string
  p = src+pos;
  q = _fstrchr(p,c);
  if (q==NULL) return 0;
  _fstrncpy(des,p,q-p);  des[q-p]='\0';
  pos = q-src;
  return 1;
}
//------------------------------------------------
int GetStrCharEnd(char far *des,char far *src, int &pos,char c)
// l½y ra mét string con cña *src tÝnh tõ vÞ trÝ pos cho tíi khi gµp
// ký tù c hoµc ¦Õn cuèi string v§ ¦µt v§o *des. Sau khi l½y pos l§ vÞ trÝ
// cña c hoµc cuèi string ('\0'). return 1 nÕu th§nh c£ng, 0 nÕu th½t b«i
{
  char far *p, *q;

  if (pos<0 || pos>=_fstrlen(src))  return 0; // kh£ng l½y ¦¥îc string
  p = src+pos;
  q = _fstrchr(p,c);
  if (q==NULL)
    q = _fstrchr(p,0);
  _fstrncpy(des,p,q-p);  des[q-p]='\0';
  pos = q-src;
  return 1;
}
//------------------------------------------------
double Value_function(char far *fn,double x)
{
  if (_fstrcmp(fn,"sqr")==0)
    return (x*x);
  if (_fstrcmp(fn,"sqrt")==0 && x>=0)
    return (sqrt(x));
  if (_fstrcmp(fn,"sin")==0)
    return (sin(x));
  if (_fstrcmp(fn,"arcsin")==0 && x>=-1 && x<=1)
    return (asin(x));
  if (_fstrcmp(fn,"cos")==0)
    return (cos(x));
  if (_fstrcmp(fn,"arccos")==0 && x>=-1 && x<=1)
    return (acos(x));
  if (_fstrcmp(fn,"ln")==0 && x>0)
    return (log(x));
  if (_fstrcmp(fn,"exp")==0)
    return (exp(x));
  return 0;
}
//------------------------------------------------
int InToken1(char c)
{
  int i;
  for (i=0; i<N_NotInToken1; i++)
    if (c==NotInToken1[i])
      return 0;
  return 1;
}
//------------------------------------------------
int GetToken1(char far *token, char far *line, int far &pos)
{
  int k,l,i;
  k = pos;
  l = _fstrlen(line);
  while (k<l && !InToken1(line[k]))
     k++;
  if (k>=l)
    {
    token[0] = '\0';  return(0);
    }
  i=0;
  while ( k<l && InToken1(line[k]) && i<MTOKEN)
    token[i++] = line[k++];
  token[i] = '\0';
  pos = k;
  return(1);
}
//------------------------------------------------
int InTokenW(char c)
{
  if (IsDigit(c)) return 1;
  if (IsLetter(c)) return 1;
  if (c=='_') return 1;
  return 0;
}
//------------------------------------------------
int IsTokenW(char far *tok)
{
  int i;
  int len = _fstrlen(tok);
  if (len <= 0) return 0;
  for (i=0; i<len; i++)
    if (!InTokenW(tok[i]))  return 0;
  return 1;
}
//------------------------------------------------
int IsIdentify(char far *tok)
{
  if (IsTokenW(tok) && IsLetter(tok[0]))
    return 1;
  return 0;
}
//------------------------------------------------
int GetTokenW(char far *token, char far *line, int far &pos)
  // l½y token Word tõ vÞ trÝ pos, nÕu ¦¥îc th× token chØ ph¶n tö l½y
  // ra ¦¥îc v§ return 1; ng¥îc l«i token[0]='\0' v§ return 0;
{
  int k,l,i;
  k = pos;  i=0;
  l = _fstrlen(line);
  while (k<l && ! InTokenW(line[k]))
     k++;
  if (k>=l)
    {
    token[0] = '\0';  return(0);
    }
  while ( k<l && InTokenW(line[k]) && i<MTOKEN)
    token[i++] = line[k++];
  token[i] = '\0';
  pos = k;
  return(1);
}
//------------------------------------------------
int InTokenE(char c)
{
  if (IsDigit(c)) return 1;
  if (IsLetter(c)) return 1;
  if (c=='_') return 1;
  if (c=='.') return 1;
  return 0;
}
//------------------------------------------------
int IsTokenE(char far *tok)
{
  int i;
  int len = _fstrlen(tok);
  if (len <= 0) return 0;
  for (i=0; i<len; i++)
    if (!InTokenE(tok[i]))  return 0;
  return 1;
}
//------------------------------------------------
int GetTokenE(char far *token, char far *line, int far &pos)
  // l½y token Expression tõ vÞ trÝ pos, nÕu ¦¥îc th× token chØ ph¶n tö l½y
  // ra ¦¥îc v§ return 1; ng¥îc l«i token[0]='\0' v§ return 0;
{
  int k,l,i;
  k = pos;  i=0;
  l = _fstrlen(line);
  while (k<l && (line[k]==' '))
     k++;
  if (k>=l)
    {
    token[0] = '\0';  return(0);
    }
  switch (line[k])
    {
    case '=':
    case '(':
    case ')':
    case '^':
    case '*':
    case '/':
    case '+':
    case '-': { token[i++] = line[k++]; token[i] = '\0';
		pos = k; return(1);
	      }
    }
  while (k<l && !InTokenE(line[k]))
     k++;
  if (k>=l)
    {
    token[0] = '\0';  return(0);
    }
  while ( k<l && InTokenE(line[k]) )
    token[i++] = line[k++];
  token[i] = '\0';
  pos = k;
  return(1);
}
//------------------------------------------------
int InTokenHoa(char c)
{
  if (IsLetter(c))  return 1;
  if (IsDigit(c))   return 1;
  if (c=='(' || c==')')  return 1;
  if (c=='-' || c=='>')  return 1;
  return 0;
}
//------------------------------------------------
int GetTokenHoa(char far *token, char far *line, int far &pos)
// l½y 1 token cña ph¨n øng hãa häc vÝ dô : NaOH, Ca(OH)2, -->, ...
{
  int k,l,i;
  k = pos;  i=0;
  l = _fstrlen(line);
  while (k<l && !InTokenHoa(line[k]))
     k++;
  if (k>=l)
    {
    token[0] = '\0';  return 0;
    }
  while ( k<l && InTokenHoa(line[k]) && i<MTOKEN)
    token[i++] = line[k++];
  token[i] = '\0';
  pos = k;
  return 1;
}
//------------------------------------------------
int GetNgtoHoa(char far *token, char far *line, int far &pos)
// l½y ra t¢n mét nguy¢n tè
{
  int k,l,i;
  k = pos;  i=0;
  l = _fstrlen(line);
  while (k<l && !(line[k]>='A' && line[k]<='Z'))
     k++;
  if (k>=l)
    {
    token[0] = '\0';  return 0;
    }
  token[i++] = line[k++];
  while ( k<l && (line[k]>='a' && line[k]<='z') && i<MTOKEN)
    token[i++] = line[k++];
  token[i] = '\0';
  pos = k;
  return 1;
}
//------------------------------------------------
int Prior(char far *token)
{
  if (_fstrcmp(token,"=")==0)  return(0);
  if (_fstrcmp(token,"(")==0)  return(1);
  if (IsFuncName(token))  return(2);
  if (_fstrcmp(token,"+")==0 || _fstrcmp(token,"-")==0)
    return(3);
  if (_fstrcmp(token,"*")==0 || _fstrcmp(token,"/")==0)
    return(4);
  if (_fstrcmp(token,"^")==0)  return(5);
  return(-1);  // kh£ng ph¨i token toªn tö hay '('
}
//====================================================
int ConvertToRPN(char far *expr,STACK_TOKEN far *pST)
{
  STACK_TOKEN StO; // stack cªc operators v§ d½u '('
  TOKEN token,tok,pretok;
  int error = 0;
  int pos=0;

  InitStack(pST);
  InitStack(&StO);
  pretok[0] = '\0';
  while (!error && GetTokenE(token,expr,pos))
    {
    if (strcmp(token,"(")==0)
      PushToken(token,&StO);
    else if (strcmp(token,")")==0)
      {
      while (PopToken(tok,&StO) && (strcmp(tok,"(")!=0) )
	PushToken(tok,pST);
      if (strcmp(tok,"(")!=0)  error=1;
      else if (!StackEmpty(&StO) && IsFuncName(TopStack(&StO)))
	{
	PopToken(tok,&StO); PushToken(tok,pST);
	}
      }
    else if (IsOperator(token))
      {
      if (strcmp(token,"-")==0 || strcmp(token,"+")==0)
	if (_fstrcmp(pretok,"(")==0 || _fstrcmp(pretok,"=")==0 ||
	    _fstrcmp(pretok,"")==0)
	  PushToken("0",pST);
      while (!StackEmpty(&StO) && Prior(TopStack(&StO)) >= Prior(token))
	{
	PopToken(tok,&StO); PushToken(tok,pST);
	}
      PushToken(token,&StO);
      }
    else if (IsFuncName(token))  // l§ t¢n h§m
      {
      PushToken(token,&StO);
      if (!GetTokenE(tok,expr,pos)) error=1;
      else if (strcmp(tok,"(")!=0) error=1;
      else PushToken(tok,&StO);
      }
    else  // l§ toªn h«ng
      PushToken(token,pST);
    strcpy(pretok,token);
    }    // kÕt thóc while
  if (!error)
    while (!error && !StackEmpty(&StO))
      {
      PopToken(tok,&StO);
      if (strcmp(tok,"(")==0)  error=1;
      PushToken(tok,pST);
      }
  if (StackEmpty(pST))  error = 1;
  return (!error);
}  // ConvertToRPN
//========================================================
TNODE far * ConvertRPN_Tree(STACK_TOKEN ST)
{
  TNODE far * Tr, far *p, far *q;
  TOKEN token;
  TNODE far *Ap[80];  int np=0;
  STACK_TOKEN far * pST;

  pST = &ST;
  Tr = NULL;

  while (PopToken(token,pST))
    {
    p = (TNODE far *)farmalloc(sizeof(TNODE));
    _fstrcpy(p->token,token); p->L=NULL; p->R=NULL;
    // t×m vÞ trÝ ¦Ó g¯n TNODE míi t«o ra
    if (np==0)   Tr=p;
    else
      {
      q = Ap[np-1];
      if (IsFuncName(q->token))
	{
	--np;  // l½y chØ ¦iÓm ph¶n tö c¶n toªn h«ng ra khái danh sªch
	q->R = p;
	}
      else if (IsOperator(q->token))
	if (q->R == NULL)  q->R = p;
	else
	  {
	  q->L = p; --np;
	  }
      }
    // xem cã c¶n ¦µt th¢m chØ ¦iÓm ¦Ønh c¶n toªn h«ng v§o danh sªch kh£ng
    if (IsOperator(token) || IsFuncName(token))
      Ap[np++] = p;
    }  // while
  return(Tr);
}
//========================================================
int ConvertFromTree(char far *expr,TNODE far *Tr)
// xem nh÷ng tr¥êng hîp n§o c¶n ngoµc, nh÷ng tr¥êng hîp n§o kh£ng c¶n ngoµc:
// - token c½p tr¢n l§ t¢n h§m
// - token hiÖn t«i l§ toªn tö cã ¦é ¥u ti¢n th½p h¤n token c½p tr¢n
// - l¥u ý token l§ toªn tö '+' hoµc '-' mét ng£i (tøc l§ 2 ng£i víi toªn
//   h«ng thø nh½t l§ 0)
{
  char S[128];

  _fstrcpy(expr,"");
  if (Tr == NULL)  return 0;
  if (IsFuncName(Tr->token))
    {
    ConvertFromTree(S,Tr->R);
    _fstrcat(expr,Tr->token);  _fstrcat(expr,"(");
    _fstrcat(expr,S);  _fstrcat(expr,")");
    return 1;
    }
  if (IsOperator(Tr->token))
    {
    if (Tr->L != NULL && IsOperator(Tr->L->token))
      if ( Prior(Tr->token) > Prior(Tr->L->token) )
	{
	_fstrcat(expr,"(");
	ConvertFromTree(S,Tr->L); _fstrcat(expr,S);
	_fstrcat(expr,")");
	}
      else
	{
	ConvertFromTree(S,Tr->L); _fstrcat(expr,S);
	}
    else if (!(_fstrcmp(Tr->token,"+")==0 || _fstrcmp(Tr->token,"-")==0)
	     || _fstrcmp(Tr->L->token,"0")!=0)
      {
      ConvertFromTree(S,Tr->L); _fstrcat(expr,S);
      }
    _fstrcat(expr,Tr->token);
    if (Tr->R != NULL && IsOperator(Tr->R->token))
      if ( Prior(Tr->token) > Prior(Tr->R->token) ||
	 ( Prior(Tr->token)==Prior(Tr->R->token) &&
	 (_fstrcmp(Tr->token,"/")==0 || _fstrcmp(Tr->R->token,"/")==0 ||
	  _fstrcmp(Tr->token,"-")==0 || _fstrcmp(Tr->R->token,"-")==0)))
	{
	_fstrcat(expr,"(");
	ConvertFromTree(S,Tr->R); _fstrcat(expr,S);
	_fstrcat(expr,")");
	}
      else
	{
	ConvertFromTree(S,Tr->R); _fstrcat(expr,S);
	}
    else if (!(_fstrcmp(Tr->token,"+")==0 || _fstrcmp(Tr->token,"-")==0)
	     || _fstrcmp(Tr->R->token,"0")!=0)
      {
      ConvertFromTree(S,Tr->R); _fstrcat(expr,S);
      }
    return 1;
    }
  _fstrcat(expr,Tr->token);
  return 1;
}
//========================================================
void FreeTreeTnode(TNODE far * &Tr)
{
  if (Tr!=NULL)
    {
    FreeTreeTnode(Tr->L); FreeTreeTnode(Tr->R);
    farfree(Tr); Tr=NULL;
    }
}
//========================================================
double Value_TreeTnode(TNODE far * Tr)
{

  if (Tr==NULL)  return 0;
  // tr¥êng hîp token ¦µc biÖt l§ pi
  if (_fstrcmp(Tr->token,"pi") == 0)
    return (Pi());
  // tr¥êng hîp toªn tö +,-,*,/,^
  if (_fstrcmp(Tr->token,"+")==0)
    return (Value_TreeTnode(Tr->L) + Value_TreeTnode(Tr->R));
  if (_fstrcmp(Tr->token,"-")==0)
    return (Value_TreeTnode(Tr->L) - Value_TreeTnode(Tr->R));
  if (_fstrcmp(Tr->token,"*")==0)
    return (Value_TreeTnode(Tr->L) * Value_TreeTnode(Tr->R));
  if (_fstrcmp(Tr->token,"/")==0)
    if (Value_TreeTnode(Tr->R) != 0)
      return (Value_TreeTnode(Tr->L) / Value_TreeTnode(Tr->R));
    else
      return 0;
  if (_fstrcmp(Tr->token,"^")==0)
    return (pow(Value_TreeTnode(Tr->L),Value_TreeTnode(Tr->R)));
  // t¢n h§m
  if (IsFuncName(Tr->token))
    return (Value_function(Tr->token,Value_TreeTnode(Tr->R)));
  // tr¥êng hîp l§ token sè
  if (atof(Tr->token)!=0)
    return (atof(Tr->token));
  return 0;
}
//========================================================
double Value_expr(char far * s)
// tÝnh giª trÞ cña biÓu thøc h¬ng
{
  TNODE far *Tr;
  STACK_TOKEN ST;
  double res;
  ConvertToRPN(s,&ST);
  Tr = ConvertRPN_Tree(ST);
  res = Value_TreeTnode(Tr);
  FreeTreeTnode(Tr);
  return (res);
}
//========================================================
int SearchToken(char far *token,TNODE far * Tr)
{
  if (Tr==NULL)  return 0;
  if (_fstrcmp(token,Tr->token)==0)  return 1;
  if (SearchToken(token,Tr->L) || SearchToken(token,Tr->R))
    return 1;
  return 0;
}
//========================================================
void Exchange_LR(TNODE far * &Tr)
{
  TNODE far *p;
  p=Tr->L; Tr->L=Tr->R; Tr->R=p;
}
//========================================================
int ReduceTreeTnode(TNODE far *&Tr)
{
  TNODE far *p;
  TOKEN tok;
  // u-(-b) chuyÓn th§nh u+b
  if (Tr!=NULL && Tr->R!=NULL && Tr->R->L!=NULL &&
   (_fstrcmp(Tr->token,"-")==0 && _fstrcmp(Tr->R->token,"-")==0 &&
     _fstrcmp(Tr->R->L->token,"0")==0) )
    {
    p = Tr;
    Tr=Tr->R;  FreeTreeTnode(Tr->L);  Tr->L=p->L; _fstrcpy(Tr->token,"+");
    p->L=NULL; p->R=NULL; FreeTreeTnode(p);
    return 1;
    }
  // rót gän h§m v§ h§m ng¥îc
  if (IsFuncName(Tr->token) && InvertFuncName(Tr->token,tok) &&
     _fstrcmp(Tr->R->token,tok)==0 )
    {
    p = Tr;
    Tr=Tr->R->R;
    p->R->R=NULL; FreeTreeTnode(p);
    return 1;
    }
  return 0;
}
//========================================================
int Move_LL(TNODE far * &Tr)
{
  TNODE far * p;
  if (Tr==NULL || Tr->L==NULL)  return 0;
  if (_fstrcmp(Tr->token,"=")!=0) return 0;
  if (_fstrcmp(Tr->L->token,"+")==0)
    {
    p = Tr->L;  Tr->L = p->R;
    p->R = p->L; p->L=Tr->R; _fstrcpy(p->token,"-");
    Tr->R=p;  return 1;
    }
  if (_fstrcmp(Tr->L->token,"-")==0)
    {
    p = Tr->L;  Tr->L = p->R;
    p->R = Tr->R;    Tr->R=p;  return 1;
    }
  if (_fstrcmp(Tr->L->token,"*")==0)
    {
    p = Tr->L;  Tr->L = p->R;
    p->R = p->L; p->L=Tr->R; _fstrcpy(p->token,"/");
    Tr->R=p;  return 1;
    }
  if (_fstrcmp(Tr->L->token,"/")==0)
    {
    p = Tr->L;  Tr->L = p->R;
    p->R = Tr->R;    Tr->R=p;  return 1;
    }
  return 0;
}
int Move_RL(TNODE far * &Tr)
{
  TNODE far * p;
  if (Tr==NULL || Tr->R==NULL)  return 0;
  if (_fstrcmp(Tr->token,"=")!=0) return 0;
  if (_fstrcmp(Tr->L->token,"+")==0 || _fstrcmp(Tr->L->token,"-")==0 ||
     _fstrcmp(Tr->L->token,"*")==0 || _fstrcmp(Tr->L->token,"/")==0)
    {
    p = Tr->L;  Tr->L = p->L;
    p->L=Tr->R;
    if (_fstrcmp(p->token,"+")==0)  _fstrcpy(p->token,"-");
    else if (_fstrcmp(p->token,"-")==0)  _fstrcpy(p->token,"+");
    else if (_fstrcmp(p->token,"*")==0)  _fstrcpy(p->token,"/");
    else if (_fstrcmp(p->token,"/")==0)  _fstrcpy(p->token,"*");
    Tr->R=p;
    return 1;
    }
  if (_fstrcmp(Tr->L->token,"^")==0)
    if (_fstrcmp(Tr->L->R->token,"2")==0)
      {
      p = Tr->L;  Tr->L = p->L;
      p->L=NULL; FreeTreeTnode(p->R); _fstrcpy(p->token,"sqrt");
      p->R=Tr->R;  Tr->R=p;
      return 1;
      }
  return 0;
}
int Move_LR(TNODE far * &Tr)
{
  int res;
  Exchange_LR(Tr);
  res = Move_LL(Tr);
  Exchange_LR(Tr);
  return (res);
}
int Move_RR(TNODE far * &Tr)
{
  int res;
  Exchange_LR(Tr);
  res = Move_RL(Tr);
  Exchange_LR(Tr);
  return res;
}
//========================================================
void Expr_Token(TNODE far * &Tr,char far *token)
{
  if (Tr==NULL || token==NULL) return;
  if (_fstrcmp(Tr->token,"=")!=0) return;
  if (!SearchToken(token,Tr->L) && !SearchToken(token,Tr->R))
    return;
  if (SearchToken(token,Tr->L))
    {
    TNODE far * p;
    p = Tr->L;
    if (_fstrcmp(p->token,token)==0) return;
    if (IsFuncName(p->token))
      {
      TOKEN tok;
      if (!InvertFuncName(p->token,tok))  return;
      Tr->L=p->R; p->R=Tr->R; _fstrcpy(p->token,tok); Tr->R=p;
      Expr_Token(Tr,token);
      }
    if (!SearchToken(token,p->R))
      { Move_RL(Tr); Expr_Token(Tr,token);
      }
    if (!SearchToken(token,p->L))
      { Move_LL(Tr); Expr_Token(Tr,token);
      }
    }
  else if (SearchToken(token,Tr->R))
    {
    Exchange_LR(Tr); Expr_Token(Tr,token);
    }
}
//========== STACK_TOKEN =====================
void InitStack(STACK_TOKEN far *pST)
{
  pST->n = 0;
}
int StackEmpty(STACK_TOKEN far *pST)
{
  if (pST->n < 1) return 1;
  return 0;
}

int PushToken(char far *token,STACK_TOKEN far *pST)
{
  if (pST->n >= MAX_STACK_TOKEN) return 0;
  _fstrcpy(pST->A[pST->n],token);
  pST->n += 1;
  return 1;
}
int PopToken(char far *token,STACK_TOKEN far *pST)
{
  if (pST->n <= 0) return 0;
  _fstrcpy(token,pST->A[pST->n-1]);
  pST->n -= 1;
  return 1;
}

char far * TopStack(STACK_TOKEN far *pST)
{
  if (pST->n > 0) return((char far *)pST->A[pST->n-1]);
  return (NULL);
}
//--------------------------------------------
double Pi()
{
  return (acos(-1));
}
//============================================
