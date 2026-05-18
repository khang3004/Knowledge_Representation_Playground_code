/*----------------------------------------------------------*/
/*                                                          */
/*   Turbo Vision 1.0                                       */
/*   Copyright (c) 1991 by Borland International            */
/*                                                          */
/*   Turbo Vision TVEDIT header file                        */
/*----------------------------------------------------------*/

class TMenuBar;
class TStatusLine;
class TEditWindow;
class TDialog;

const
  cmOpen       = 100,
  cmNew        = 101,
  cmChangeDrct = 102,
  cmDosShell   = 103,
  cmCalculator = 104,
  cmShowClip   = 105,

  cmGivePro  = 106,
  cmSolvePro = 107,
  cmViewPu = 108,
  cmEditPu = 109,

  cmGeneralHlp = 110,
  cmProblemHlp = 111,
  cmPuHlp = 112;

class TEditorApp : public TApplication
{

public:

    TEditorApp();

    virtual void handleEvent( TEvent& event );
    static TMenuBar *initMenuBar( TRect );
    static TStatusLine *initStatusLine( TRect );
    virtual void outOfMemory();

private:

    TEditWindow *openEditor( const char *fileName, Boolean visible );
    void fileOpen(const char *fname);
    void fileNew();
    void changeDir();
    void dosShell();
    void showClip();
    void tile();
    void cascade();

    void solveProblem();
    void GiveProblem();

    void fileView(const char *fname);  // fname cã thÓ dïng ký hiÖu * v§ ?
    void openView(const char *fn);
    void fileDelete(const char *fname);  // fname cã thÓ dïng ký hiÖu * v§ ?
};

extern TEditWindow *clipWindow;

ushort execDialog( TDialog *d, void *data );
TDialog *createFindDialog();
TDialog *createReplaceDialog();
ushort doEditDialog( int dialog, ... );

TDialog *createInputLineDialog();
