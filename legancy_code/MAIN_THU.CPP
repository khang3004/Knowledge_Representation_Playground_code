#include "SET32.hpp"
#include "token.hpp"
#include "HOA.HPP"

#include <stdio.h>

void main()
{
  FILE *fp;
  int i;
  set32N A,B;
  INT_ARR Solution;
  PU_HH pu;

  Init("PU_HOA.TXT");

  if ( !ReadDe("DE.TXT",A,B) )
    return;
  fp = fopen("TAM1.TXT","wt");
  if (fp==NULL)
    return;
  GiaiDe_DieuChe(fp,A,B);

  GiaiDe_DayChuyen(fp,"ZnS --> SO2 --> H2SO3");
  GiaiDe_DayChuyen(fp,"ZnS --> ZnO --> ZnCl2");

  fclose(fp);
  FreeVar();
}

//-----------------------------------------
void fwrite_Ngto(FILE far *fp);

void main1()
{
  FILE *fp;
  int i;
  char fname[32];
  PU_HH pu;

  printf("t¢n file ghi cªc ph¨n øng: ");  gets(fname);
  Init(fname);
  fp = fopen("TAM1.TXT","wt");
  if (fp==NULL)
    return;
  fprintf(fp,"Sè ch½t = %d\n",SoChat);
  fprintf(fp,"Sè ph¨n øng = %d\n",SoPu);
  fprintf(fp,"Sè nguy¢n tè = %d\n",SoNgto);
  for (i=0; i<SoPu; i++)
    {
    GetPu(pu,i);  fwrite_Pu(fp,pu);
    }

  fclose(fp);
  FreeVar();
}

void fwrite_Ngto(FILE far *fp)
{
  int i;
  fprintf(fp,"\nCªc nguy¢n tè :\n");
  for (i=0; i<SoNgto; i++)
    {
    if (i % 10 == 0)  fprintf(fp,"\n");
    fprintf(fp,"%s ",ListNgto[i].token);
    }
  fprintf(fp,"\n");
}

