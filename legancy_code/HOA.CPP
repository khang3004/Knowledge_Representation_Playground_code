#include "HOA.HPP"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <alloc.h>


//-------- Cªc biÕn khai bªo trong HOA.CPP -----------
// cªc biÕn n½y sÏ ¦¥îc khëi t«o bëi h§m Init_HOA()
  CHAT_HH *ListChat;  // danh sªch ch½t
  int SoChat; // sè ch½t
  NG_TO *ListNgto; // danh sªch nguy¢n tè
  int SoNgto; // sè nguy¢n tè
  PU_HH far *ListPu;
  int SoPu;
//----------------------------------------------------


//================= Cªc h§m ===================

//---------------------------------------------
int Init(char *fname)
// tõ cªc ph¨n øng ghi trong file *fname, khëi t«o cªc biÕn ë tr¢n
{
  char s[256];
  FILE *fp, *fpu;
  NODE far * p = NULL, far * HeadChat=NULL;
  TOKEN tok;  // mét c£ng thøc ch½t hãa häc, vd: H2O
  PU_HH pu;
  int pos,Lflag,i;

  fp = fopen(fname,"rt");
  if (fp==NULL)  return 0;

  // giª trÞ ban ¦¶u cña cªc biÕn
  ListChat = NULL;  SoChat=0;
  ListNgto = NULL;  SoNgto=0;
  ListPu = NULL;  SoPu=0;
  // Ÿäc file ghi cªc ph¨n øng (mçi ph¨n øng b¯t ¦¶u b¬ng d½u *) v§ khëi
  // t«o cªc biÕn: SoChat, SoPu, ListChat
  fgets(s,256,fp);
  while (!feof(fp))
    {
    if (s[0]=='*')
      {
      SoPu++;
      pos = 0;
      while (GetTokenHoa(tok,s,pos))
	if (_fstrcmp(tok,"-->")!=0 && !InListNode(tok,HeadChat))
	  {
	  SoChat++;
	  p = (NODE far *) farmalloc(sizeof(NODE));
	  if (p==NULL)
	    return 0;
	  _fstrcpy((p->chat).token,tok);  p->next = HeadChat;  HeadChat = p;
	  }
      }
    fgets(s,256,fp);
    } // while
  // xin c½p phªt memory cho ListChat, ¦µt giª trÞ, freemem cho HeadChat
  ListChat = (CHAT_HH far *) farmalloc(sizeof(CHAT_HH)*SoChat);
  if (ListChat==NULL)
    return 0;
  p = HeadChat;
  for (i=0; i<SoChat; i++)
    {
    ListChat[i] = p->chat;  ListChat[i].name[0]='\0';
    p = p->next;
    }
  FreeListNode(HeadChat);

  // Khëi t«o biÕn List ph¨n øng ghi v§o file PU_HH.DAT
  fpu = fopen("PU_HH.DAT","wb");
  if (fpu==NULL)  return 0;

  fseek(fp,0,0);  // trë l«i tõ ¦¶u file
  fgets(s,256,fp);
  while (!feof(fp))
    {
    if (s[0]=='*')
      {
      EmptyN(pu.Left);  EmptyN(pu.Right);
      pos = 0;  Lflag=1;
      while (GetTokenHoa(tok,s,pos))
	if (_fstrcmp(tok,"-->")==0)
	  Lflag=0; // sang vÕ trªi cña ph¨n øng
	else if (Lflag==1)
	  IncludeN(NumOfTokenHoa(tok,ListChat,SoChat),pu.Left);
	else
	  IncludeN(NumOfTokenHoa(tok,ListChat,SoChat),pu.Right);
      fwrite(&pu,LEN_PU,1,fpu);
      }   // if
    fgets(s,256,fp);
    } // while
  fclose(fp);  fclose(fpu);
/*
  // khëi t«o cªc biÕn ListNgto, SoNgto
  HeadChat = NULL;  SoNgto=0;
  for (i=0; i<SoChat; i++)
    {
    pos = 0;
    while (GetNgtoHoa(tok,ListChat[i].token,pos))
      if (!InListNode(tok,HeadChat))
	{
	SoNgto++;
	p = (NODE far *) farmalloc(sizeof(NODE));
	if (p==NULL)
	  return 0;
	_fstrcpy((p->chat).token,tok);  p->next = HeadChat;  HeadChat = p;
	}
    }
  // xin c½p phªt memory cho ListNgto, ¦µt giª trÞ, freemem cho HeadChat
  ListNgto = (CHAT_HH far *) farmalloc(sizeof(CHAT_HH)*SoNgto);
  if (ListNgto==NULL)
    return 0;
  p = HeadChat;
  for (i=0; i<SoNgto; i++)
    {
    ListNgto[i] = p->chat;  ListNgto[i].name[0]='\0';
    p = p->next;
    }
  FreeListNode(HeadChat);
*/
  return 1;
} // Init()
//---------------------------------------------
void FreeVar()
// free ph¶n bé nhí ¦© xin c½p phªt cho cªc biÕn bëi h§m Init()
{
  if (ListChat != NULL)
    farfree(ListChat);
  if (ListPu != NULL)
    farfree(ListPu);
  if (ListNgto != NULL)
    farfree(ListNgto);
  ListChat = NULL;  ListPu = NULL;  ListNgto =NULL;
}
//---------------------------------------------
int ReadDe(char *fname,set32N A,set32N B)
{
  FILE far *fp;
  char line[128];
  TOKEN token;
  int pos, flagI, flagO, flagE;

  if ((fp = fopen(fname,"rt")) == NULL)
    return 0;
  // T×m vÞ trÝ b¯t ¦¶u input
  flagI=0;
  fgets(line,128,fp);
  while (!feof(fp))
    {
    pos=0;
    GetTokenHoa(token,line,pos);
    if (strcmp(token,"input")==0)
      { flagI = 1; break;
      }
    fgets(line,128,fp);
    }
  if (!flagI) return 0;
  // ¦äc gi¨ thiÕt A cho tíi khi gµp tõ 'output'
  EmptyN(A); flagO=0;
  fgets(line,128,fp);
  while (!feof(fp))
    {
    pos=0;
    while (GetTokenHoa(token,line,pos))
      if (strcmp(token,"output")==0)
	{ flagO = 1; goto label_output;
	}
      else if (strcmp(token,"")!=0)
	IncludeN(NumOfTokenHoa(token,ListChat,SoChat),A);
    fgets(line,128,fp);
    } // while ngo§i
label_output:
  if (!flagO) return 0;
  // ¦äc kÕt lu¾n B
  EmptyN(B); flagE=0;
  fgets(line,128,fp);
  while (!feof(fp))
    {
    pos=0;
    while (GetTokenHoa(token,line,pos))
      if (strcmp(token,"end")==0)
	{ flagE = 1; goto label_end;
	}
      else if (strcmp(token,"")!=0)
	IncludeN(NumOfTokenHoa(token,ListChat,SoChat),B);
    fgets(line,128,fp);
    } // while ngo§i
label_end:
  if (!flagE) return 0;
  return 1;
} // ReadDe
//---------------------------------------------
int ReadDe_Daychuyen(char * fname,char *s)
{
  int flagI,pos;
  TOKEN token;
  FILE *fp;

  if ((fp = fopen(fname,"rt")) == NULL)
    return 0;
  flagI=0;
  fgets(s,128,fp);
  while (!feof(fp))
    {
    pos=0;    GetTokenHoa(token,s,pos);
    if (strcmp(token,"input")==0)
      { flagI = 1; break;
      }
    fgets(s,128,fp);
    }
  if (!flagI)  return 0;

  fgets(s,128,fp);
  while (!feof(fp))
    {
    pos=0;    GetTokenHoa(token,s,pos);
    if (strcmp(token,"")!=0)
      return 1;
    fgets(s,128,fp);
    }
  return 0;
}
//============ Cªc h§m phôc vô h§m Init() =================

//---------------------------------------------
void  FreeListNode(NODE far * &Head)
{
  while (Head != NULL)
    {
    FreeListNode(Head->next);
    farfree(Head);
    Head = NULL;
    }
}
//---------------------------------------------
int InListNode(char far *tok,NODE far *Head)
{
  NODE far * p;
  p = Head;
  while (p != NULL)
    if (_fstrcmp(tok,(p->chat).token) == 0)
      return 1;
    else
      p = p->next;
  return 0;
}
//---------------------------------------------
int NumOfTokenHoa(char far *tok,CHAT_HH far *List,int sochat)
{
  int i;
  for (i=0; i<sochat; i++)
    if (_fstrcmp(tok,List[i].token) == 0)
      return i;
  return -1;  //kh£ng tok trong list
}
//---------------------------------------------
void FromPu(char *pu,set32N Left,set32N Right)
{
  TOKEN tok;
  int pos,Lflag;

  EmptyN(Left);   EmptyN(Right);
  if (pu[0]=='*')
      {
      pos = 0;  Lflag=1;
      while (GetTokenHoa(tok,pu,pos))
	if (_fstrcmp(tok,"-->")==0)
	  Lflag=0; // sang vÕ trªi cña ph¨n øng
	else if (Lflag==1)
	  IncludeN(NumOfTokenHoa(tok,ListChat,SoChat),Left);
	else
	  IncludeN(NumOfTokenHoa(tok,ListChat,SoChat),Right);
      }   // if
}
//---------------------------------------------
int GetPu(PU_HH &pu,int i)
// l½y ra ph¨n øng thø i
{
  FILE *fp;

  if (i<0 || i>=SoPu)
    return 0;
  fp = fopen("PU_HH.DAT","rb");
  if (fp==NULL)
    return 0;
  if (fseek(fp,(long)LEN_PU*i,0) != 0)
    return 0;
  fread(&pu,LEN_PU,1,fp);
  fclose(fp);

  return 1;
}
//-------------------------------------------
void fwrite_Pu(FILE far *fp,PU_HH pu)
{
    fprintf(fp,"* ");
    fwrite_SetChat(fp,pu.Left,'+');
    fprintf(fp," --> ");
    fwrite_SetChat(fp,pu.Right,'+');
    fprintf(fp,"\n");
}
//-------------------------------------------
void fwrite_SetChat(FILE far *fp,set32N A,char c)
{
  int j,flag;
  flag = 1;
  for (j=0; j<SoChat; j++)
    if (BitN(j,A))
      if (flag) // l¶n ¦¶u
	{ fprintf(fp,"%s ",ListChat[j].token);  flag = 0;
	}
      else
	fprintf(fp,"%c %s ",c,ListChat[j].token);
} // fwrite_SetChat
//-------------------------------------------
int Apply_Pu(int i,set32N A)
{
  PU_HH pu;
  if (i<0 || i>=SoPu)
    return 0;
  GetPu(pu,i);
  if (InN(pu.Left,A))
    return 1;
  return 0;
}
//-------------------------------------------
void D_A(INT_ARR D,set32N A,set32N DA)
{
  int i;
  PU_HH pu;
  AssignSet32N(DA,A);
  for (i=0; i < D.n; i++)
    if (GetPu(pu,D.A[i]))
      if ( InN(pu.Left,DA) )
	UnionN(DA,pu.Right,DA);
  return;
}
//-------------------------------------------
void Closure(set32N A, set32N _A)
{
  set32N B;
  int i;
  PU_HH pu;
  do
    {
    AssignSet32N(B,A);
    for (i=0; i<SoPu; i++)
      if (GetPu(pu,i))
	if ( InN(pu.Left,A) )
	  UnionN(A,pu.Right,A);
    }
  while ( !EqualN(B,A) );
  AssignSet32N(_A,A);
}
//-------------------------------------------
int Solvable(set32N GT, set32N KL)
{
  set32N baodong;
  Closure(GT,baodong);
  return( InN(KL,baodong) );
}
//-------------------------------------------
int Is_Solution(INT_ARR D,set32N A,set32N B)
{
  set32N DA;
  D_A(D,A,DA);
  if (InN(B,DA))
    return 1;
  return 0;
}
//-------------------------------------------
int Find_1Solution(set32N GT, set32N KL, INT_ARR far &Solution)
{
  int Solution_found = 0;
  set32N A,B,Aold;
  int i;
  PU_HH pu;

  AssignSet32N(A,GT);  AssignSet32N(B,KL);
  // b¥íc 1
  Solution.n = 0;
  // b¥íc 2
  if (InN(B,A))  Solution_found = 1;
  // b¥íc 3
  do
    {
    AssignSet32N(Aold,A);
    for (i=0; i<SoPu; i++)
      {
      if (Solution_found)  break;
      if (GetPu(pu,i))
	if ( InN(pu.Left,A) )
	  {
	  UnionN(A,pu.Right,A);
	  Solution.A[Solution.n++] = i;
	  }
      if (InN(B,A))  Solution_found = 1;
      }
    }
  while (!Solution_found && !EqualN(A,Aold));

  return (Solution_found);
}
//-------------------------------------------
void Put_Int(int sttR,INT_ARR far &D)
{
  int i;
  if (D.n>=MAX_PU || D.n<0)
    return;
  for (i=D.n; i>0; i--)
    D.A[i] = D.A[i-1];
  D.n +=1;
  D.A[0] = sttR;

}
//-------------------------------------------
void Put_Int_Tail(int stt,INT_ARR far &D)
{
  if (D.n>=MAX_PU || D.n<0)
    return;
  D.A[D.n] = stt;
  D.n +=1;
}
//-------------------------------------------
void Find_Good_Solution(set32N GT,set32N KL,INT_ARR Solution,INT_ARR far &D)
{
  INT_ARR D1;
  int i,j;

  D.n=0;
  D1 = Solution;
  for (i=Solution.n-1; i>=0; i--)
    {
    D1.n = i + D.n;
    for (j=i; j<D1.n; j++)
      D1.A[j] = D.A[j-i];
    if (!Is_Solution(D1,GT,KL))
      Put_Int(Solution.A[i],D);
    }
  return;
}
//-------------------------------------------
int Find_Solution(set32N GT, set32N KL, INT_ARR far &Solution)
{
  INT_ARR D;
  if (!Find_1Solution(GT,KL,D))
    return 0;
  Find_Good_Solution(GT,KL,D,Solution);
  return 1;
}
//-------------------------------------------
int GiaiDe_DieuChe(FILE *fp,set32N GT,set32N KL)
{
  INT_ARR D;
  PU_HH pu;
  int i;

  fprintf(fp,"\nŸÒ ¦iÒu chÕ :\n");
  fprintf(fp,"\ninput:\n  ");
  fwrite_SetChat(fp,GT,' ');
  fprintf(fp,"\noutput:\n  ");
  fwrite_SetChat(fp,KL,' ');

  fprintf(fp,"\nSolution:\n\n");
  if (!Find_Solution(GT,KL,D))
    {
    fprintf(fp,"  No solution.\n");  return 0;
    }
  else
    for (i=0; i<D.n; i++)
      {
      GetPu(pu,D.A[i]);  fwrite_Pu(fp,pu);
      }
  return 1;
} // GiaiDe_Dieuche
//-------------------------------------------
int GiaiDe_DayChuyen(FILE *fp,char *s)
{
  TOKEN Chat[20];  // danh sªch ch½t trong d¡y chuyÒn
  int nChat=0;  // sè ch½t trong d¡y chuyÒn
  int i,j,pos,flag;
  TOKEN tok;
  PU_HH pu;

  fprintf(fp,"\nŸÒ d¡y chuyÒn ph¨n øng:\n  %s\n\n",s);
  fprintf(fp,"Solution:\n");
  pos = 0;  flag=0;  // flag =1 khi võa l½y ¦¥îc ch½t
  while (GetTokenHoa(tok,s,pos))
    {
    if (!flag && strcmp(tok,"-->")==0)
      {
      fprintf(fp,"  Invalid problem.\n");
      return 0;
      }
    if (flag && strcmp(tok,"-->")==0)
      flag=0;
    if (!flag && NumOfTokenHoa(tok,ListChat,SoChat) >= 0)
      {
      strcpy(Chat[nChat++],tok);  flag=1;
      }
    }
  //--- dß cªc ph¨n øng ---
  for (i=0; i<nChat-1; i++)
    {
    j=Find_Pu(Chat[i],Chat[i+1]);
    if (GetPu(pu,j))
      fwrite_Pu(fp,pu);
    else
      {
      fprintf(fp,"* Kh£ng t×m th½y ph¨n øng.\n");
      return 0;
      }
    }
  return 1;
} // GiaiDe_DayChuyen()
//-------------------------------------------
int Find_Pu(TOKEN chat1, TOKEN chat2)
{
  int i,j1,j2;
  PU_HH pu;

  for (i=0; i<SoPu; i++)
    {
    j1=NumOfTokenHoa(chat1,ListChat,SoChat);
    j2=NumOfTokenHoa(chat2,ListChat,SoChat);
    GetPu(pu,i);
    if ( BitN(j1,pu.Left) && BitN(j2,pu.Right) )
      return i;
    }
  return -1;
}
//-------------------------------------------
int SolveTo(FILE *fp,char *fname)
// ¦äc ¦Ò tõ file *fname v§ ghi b§i gi¨i v§o *fp. retrun 1 nÕu gi¨i ¦¥îc
{
  int flag, loai;
  set32N A,B;
  char s[256];

  Init("PU_HOA.TXT");

  loai = LoaiDe(fname);
  flag =0;
  switch (loai)
    {
    case 1:
      if ( !ReadDe(fname,A,B) )
	return 0;
      flag = GiaiDe_DieuChe(fp,A,B);
      break;
    case 2:
      ReadDe_Daychuyen(fname,s);
      flag = GiaiDe_DayChuyen(fp,s);
      break;
    }

  FreeVar();
  return flag;
}  // SolveTo
//-------------------------------------------
int LoaiDe(char *fname)
// 0: kh£ng ¦äc ¦¥îc ¦Ò, 1:DiÒu chÕ  2:d¡y chuyÒn ph¨n øng, ...
{
  FILE *fp;
  char s[128];
  TOKEN tok;
  int pos,j;

  if ( (fp=fopen(fname,"rt")) == NULL )
    return 0;

  fgets(s,128,fp);
  while (!feof(fp))
    {
    pos=0;
    GetTokenW(tok,s,pos);
    if (strcmp(tok,"problem")==0)
      {
      GetTokenW(tok,s,pos);      j = atoi(tok);
      return j;
      }
    fgets(s,128,fp);
    }
  return 0;
}