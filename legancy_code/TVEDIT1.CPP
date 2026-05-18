/*----------------------------------------------------------*/
/*                                                          */
/*   Turbo Vision 1.0                                       */
/*   Copyright (c) 1991 by Borland International            */
/*                                                          */
/*   Turbo Vision TVEDIT source file                        */
/*----------------------------------------------------------*/

#define Uses_TApplication
#define Uses_TEditWindow
#define Uses_TDeskTop
#define Uses_TRect
#define Uses_TEditor
#define Uses_TFileEditor
#define Uses_TFileDialog
#define Uses_TChDirDialog

//-------------- mine ----------------
#include <stdio.h>
#include <conio.h>
#include <ctype.h>
#include <string.h>
#include "HOA.HPP"


#define Uses_MsgBox

#if !defined( __FILEVIEW_H )
#include "FileView.h"
#endif  // __FILEVIEW_H

//------------------------------------

#include <tv.h>

#include "tvedit.h"

#include <stdlib.h>
#include <stdarg.h>
#include <strstrea.h>
#include <iomanip.h>

TEditWindow *clipWindow;

TEditWindow *TEditorApp::openEditor( const char *fileName, Boolean visible )
{
    TRect r = deskTop->getExtent();
    TView *p = validView( new TEditWindow( r, fileName, wnNoNumber ) );
    if( !visible )
	p->hide();
    deskTop->insert( p );
    return (TEditWindow *)p;
}

TEditorApp::TEditorApp() :
    TProgInit( TEditorApp::initStatusLine,
	       TEditorApp::initMenuBar,
	       TEditorApp::initDeskTop
	     ),
    TApplication()
{

    TCommandSet ts;
    ts.enableCmd( cmSave );
    ts.enableCmd( cmSaveAs );
    ts.enableCmd( cmCut );
    ts.enableCmd( cmCopy );
    ts.enableCmd( cmPaste );
    ts.enableCmd( cmClear );
    ts.enableCmd( cmUndo );
    ts.enableCmd( cmFind );
    ts.enableCmd( cmReplace );
    ts.enableCmd( cmSearchAgain );
    disableCommands( ts );

    TEditor::editorDialog = doEditDialog;
    clipWindow = openEditor( 0, False );
    if( clipWindow != 0 )
        {
        TEditor::clipboard = clipWindow->editor;
	TEditor::clipboard->canUndo = False;
	}
}

void TEditorApp::fileOpen(const char *fname)
{
    char fileName[MAXPATH];
    strcpy( fileName, fname );

    if( execDialog( new TFileDialog( fname, "Open file",
	    "~N~ame", fdOpenButton, 100 ), fileName) != cmCancel )
	openEditor( fileName, True );
}

void TEditorApp::fileNew()
{
    openEditor( 0, True );
}

void TEditorApp::changeDir()
{
    execDialog( new TChDirDialog( cdNormal, 0 ), 0 );
}

void TEditorApp::dosShell()
{
    suspend();
    system("cls");
    cout << "Type EXIT to return...";
    system( getenv( "COMSPEC"));
    resume();
    redraw();
}

void TEditorApp::showClip()
{
    clipWindow->select();
    clipWindow->show();
}

void TEditorApp::tile()
{
    deskTop->tile( deskTop->getExtent() );
}

void TEditorApp::cascade()
{
    deskTop->cascade( deskTop->getExtent() );
}

void TEditorApp::GiveProblem()
{
  system("copy problem.txt untitle.txt /Y");
  openEditor( "untitle.txt", True );
}

void TEditorApp::solveProblem()
{
  FILE far * fp;
  int flag;
  char fn[80], fname[80];

  TDialog * tdlg = createInputLineDialog();
  strcpy(fname,"DE");
  if (execDialog(tdlg,fname) == cmCancel)
    return;

  // më file ghi lêi gi¨i
  strcpy(fn,fname);  strcat(fn,".SOL");
  fp = fopen(fn,"wt");
  if (fp==NULL) return;

  strcpy(fn,fname);  strcat(fn,".TXT");    // ¦µt fn l§ t¢n file ¦Ò
  flag = SolveTo(fp,fn);
  fclose(fp);
  if (flag)
    {
    messageBox("problem is solved.", mfInformation | mfOKButton );
    strcpy(fn,fname);  strcat(fn,".SOL");
    openView( fn );
    }
  else
    messageBox("problem is no solution.", mfInformation | mfOKButton );
}

void TEditorApp::fileView(const char *fname)
{
    TFileDialog *d= (TFileDialog *)validView(
	new TFileDialog( fname, "Open a File", "~N~ame", fdOpenButton, 100 ));
    if( d != 0 && deskTop->execView( d ) != cmCancel )
	{
	char fileName[MAXPATH];
	d->getFileName( fileName );
	TView *w= validView( new TFileWindow( fileName ) );
	if( w != 0 )
	    deskTop->insert(w);
	}
    destroy( d );
}

void TEditorApp::openView(const char *fn)
{
  TView *w= validView( new TFileWindow( fn ) );
  if ( w != 0 )
    deskTop->insert(w);
}

void TEditorApp::fileDelete(const char *fname)
{
    char fileName[MAXPATH], comm[80];
    int len;
    strcpy( fileName, fname );

    if( execDialog( new TFileDialog( fname, "Delete Object file",
	    "~N~ame", fdOpenButton, 100 ), fileName) != cmCancel )
      {
      len = strlen(fileName);
      if (len<3 || toupper(fileName[len-1])!='O' || (fileName[len-2]!='.'))
	{
	messageBox("Not an object file.", mfInformation | mfOKButton );
	return;
	}
      strcpy(comm,"del ");  strcat(comm,fileName);
      if (system(comm)==0)
	messageBox("Object deleted.", mfInformation | mfOKButton );
      else
	messageBox("Object deleting error.", mfInformation | mfOKButton );
      }
}


void TEditorApp::handleEvent( TEvent& event )
{
    TApplication::handleEvent( event );
    if( event.what != evCommand )
	return;
    else
	switch( event.message.command )
	    {
	    case cmOpen:
		fileOpen("*.*");
		break;
	    case cmNew:
		fileNew();
		break;
	    case cmChangeDrct:
		changeDir();
		break;
	    case cmDosShell:
		dosShell();
		break;
	    case cmShowClip:
		showClip();
		break;
	    case cmTile:
		tile();
		break;
	    case cmCascade:
		cascade();
		break;

	    case cmGivePro:
		GiveProblem();
		break;
	    case cmSolvePro:
		solveProblem();
		break;

	    case cmViewPu:
		fileView("PU_HOA.TXT");
		break;
	    case cmEditPu:
		fileOpen("PU_HOA.TXT");
		break;
	    case cmGeneralHlp:
		// openView("General.hlp");
		break;
	    case cmProblemHlp:
		// openView("Problem.hlp");
		break;
	    case cmPuHlp:
		// openView("Object.hlp");
		break;

	    default:
		return ;
	    }
    clearEvent( event );
}

int main()
{
    TEditorApp editorApp;
    editorApp.run();
    return 0;
}

