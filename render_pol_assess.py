from fancy_round import *
from progress_reporter import *
import matplotlib.pyplot as plt

#height of the bars
height = 0.40  

#fonts
font = {'family' : 'sans serif','size'   : 11}
smallfont= {'family' : 'sans serif','size'   : 9}
tinyfont= {'family' : 'sans serif','size'   : 8}

#instructs matplotlib to use that font by default
plt.rc('font', **font)

def render_pol_cards(ders,colors,policy_descriptions,unit,size,province_list=None):
    """Renders the scorecards
    ders: dataframe indexed by (var). Column is multi-indexed: provinces x ["dWtot_currency","dKtot"]. The impact of marginally increasing var in province on dw and dK.
    policy_descriptions. Series index by variable. Explains what the policy is. eg "Decrease poverty to 0.1%" 
    colors: dataframe. Columns: ["dWtot_currency","dKtot"]. Rows: kwargs to pass to plt.barh for formatting the color bars.
    unit: dictionary such as {"multiplier":1000, "string" Thousands }. For the x label.
    province_list: provinces to plot. Should be in ders.index.
    size: Size of the policy experiment. To be multiplied by ders.
    """
    
    #By default, plots all provinces in ders.
    if province_list is None:
        province_list=ders.unstack("var").index
    
    for p in province_list:
        #Displays current province in the loop 
        progress_reporter(p)    
        
        #select current line in ders, and scales it.
        toplot = unit["multiplier"]*(ders[p].mul(size,axis=0)).dropna()  
        
        #assumes the policy is framed in terms of what increases welfare ("decrease poverty", not "increase poverty")
        toplot = toplot.mul(-np.sign(toplot.dWtot_currency),axis=0)
        toplot = toplot[["dWtot_currency","dKtot"]].sort_values("dWtot_currency",ascending=False)       

        n=toplot.shape[0]
        
        #new figure
        fig, ax = plt.subplots(figsize=(3.5,n/2))
    
        #actual plotting
        ind=np.arange(n)
        rects1 = ax.barh(ind,toplot["dKtot"],height=height, **colors.ix["dKtot"]
               )
        rects2 = ax.barh(ind+height,  toplot["dWtot_currency"],height=height, **colors.ix["dWtot_currency"]
                )

        #0 line
        plt.vlines(0, 0, n, colors="black")    
        
        # add some labels, title and axes ticks
        ax.set_xlabel(unit["string"])
        ax.set_yticks(ind+height)
        ax.set_yticklabels(policy_descriptions[toplot.index]+"     "  )
        plt.title(p);

        # remove spines
        # ax.spines['bottom'].set_color('none')
        ax.spines['right'].set_color('none')

        ax.spines['top'].set_color('none')
        ax.spines['left'].set_color("none")

        #removes ticks 
        for tic in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
        
        ax.xaxis.set_ticklabels([])

        #labels (numbers) on the bars
        autolabel(ax,rects1,colors.ix["dKtot","edgecolor"],2,**tinyfont)
        autolabel(ax,rects2,colors.ix["dWtot_currency","edgecolor"],2,**smallfont)

        #annotated "legend"
        ax.annotate("Effect on asset losses",  xy=(0,n-1+height/2),xycoords='data',ha="left",va="center",
                      xytext=(20, -5), textcoords='offset points', 
                        arrowprops=dict(arrowstyle="->",
                                        connectionstyle="arc3,rad=-0.13",color=colors.edgecolor.dKtot
                                        ), **smallfont)

        ax.annotate("Effect on welfare losses",  xy=(0,n-height),xycoords='data',ha="left",va="center",
                      xytext=(20, 3), textcoords='offset points', 
                        arrowprops=dict(arrowstyle="->",
                                        connectionstyle="arc3,rad=+0.13",color=colors.edgecolor.dWtot_currency
                                        ), **smallfont)

        #exports to pdf
        plt.savefig("cards/"+file_name_formater(p)+".pdf",
                    bbox_inches="tight" #ensures the policy label are not cropped out
                    )
            
def autolabel(ax,rects,color, sigdigits,  **kwargs):
    """attach labels to an existing horizontal bar plot. Passes kwargs to the text (font, color, etc)"""
    
    
    for rect in rects:
        
        #parameters of the rectangle
        h = rect.get_height()
        x = rect.get_x()
        y = rect.get_y()
        w = rect.get_width()
        
        #figures out if it is a negative or positive value
        value = x if x<0 else w

        ####
        # FORMATS LABEL
        
        #truncates the value to sigdigits digits after the coma.
        stri=str(fancy_round(value,sigdigits))
        
        #remove trailing zeros
        if "." in stri:
            while stri.endswith("0"):
                stri=stri[:-1]        
        
        #remove trailing dot
        if stri.endswith("."):
            stri=stri[:-1]        
        
        #space before or after (pad)
        if value<0:
            stri = stri+' '
        else:
            stri = ' '+stri

        #actual print    
        ax.text(value, y+0.4*h, stri, ha="right" if x<0 else 'left', va='center', color=color , **kwargs)

        
def file_name_formater(string):
    """Ensures string does not contain special characters so it can be used as a file name"""    
    return string.lower().replace(" ","_").replace("\\","")
       
from subprocess import Popen
import sys, os

def merge_cardfiles(list,outputname):
    """Merges individual policy card pdf to a single multi page pdf with all the cards. Requires ghostscipt."""
    #implements http://stackoverflow.com/questions/7102090/combining-pdf-files-with-ghostscript-how-to-include-original-file-names

    #builds the command for ghostscript
    command= ""
    i=1
    for name in list:
        command+="(cards/{name}) run [ /Page {page} /Title ({name}) /OUT pdfmark \n".format(name=file_name_formater(name)+".pdf",page=i)
        i+=1

    #writes the command for ghostscipt
    with open("control.ps", "w") as text_file:
        text_file.write(command)

    #runs ghostscipt in a new process
    p=Popen("gswin64c -dEPSFitPage -sDEVICE=pdfwrite -o "+outputname+" control.ps");

    print("Merging cards....")
    sys.stdout.flush()

    #waits for GS to finish
    p.communicate()
    print("Merging cards done")
    
    #deletes GS command
    os.remove("control.ps")

import  glob
from subprocess import call, Popen    
import shutil
import os

def convert_pdf_to_png()
    """Convert individual pdf scorecards to PNG. Requires imagemagick. 
    Moves the resulting png to a subolfer"""  ##TODO do this directly with mogrify
    
    #starts imagemagick in a new process 
    q=Popen("mogrify -density 150 -format png cards/*.pdf");
    print("Converting scorecards....")
    sys.stdout.flush()
    
    #waits for imagemagick to finish
    q.communicate()
    print("conversion to png done")

    ###MOVE resulting PNG to a subfolder
    
    #lists all files in cards/
    sourcepath="cards"
    source = os.listdir(sourcepath)

    #creates the destination subdir
    destinationpath = "cards/png/"
    glob.os.makedirs(destinationpath,exist_ok=True) 

    #moves each png to the subdir
    for files in source:
        if files.endswith('.png'):
            shutil.move(os.path.join(sourcepath,files), os.path.join(destinationpath,files))




    
    
