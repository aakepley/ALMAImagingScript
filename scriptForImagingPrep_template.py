#>>> ======================================================================================#
#>>>                        TEMPLATE IMAGING PREP SCRIPT                                   #
#>>> ======================================================================================#
#>>>
#>>> Updated: Fri Sep 28 09:50:52 EDT 2018

#>>>
#>>> Lines beginning with '#>>>' are instructions to the data imager
#>>> and will be removed from the script delivered to the PI. If you
#>>> would like to include a comment that will be passed to the PI, begin
#>>> the line with a single '#', i.e., standard python comment syntax.
#>>>
#>>> Helpful tip: Use the commands %cpaste or %paste to copy and paste
#>>> indented sections of code into the casa command line.
#>>>
#>>>--------------------------------------------------------------------------------------#
#>>>                     Data Preparation                                                 #
#>>> -------------------------------------------------------------------------------------#
#>>>
#>>> Below are some example commands for combining your data. All of
#>>> these commands will not be relevant for all datasets, so think about
#>>> what would be best for your data before running any commands. For
#>>> more information, see the NA Imaging Guide
#>>> (https://staff.nrao.edu/wiki/bin/view/NAASC/NAImagingScripts).
#>>>
#>>> These commands should be run prior to undertaking any imaging.
#>>>>
#>>> The NA Imaging team is working on generating best
#>>> practices for this step. Suggestions are welcome!  Please send to
#>>> akepley@nrao.edu and she'll forward them on to the NA Imaging team.
#>>>
#>>>

######################################
# Splitting off the calibrated data

#>>> Produce a *.split.cal file from pipeline products to match historic
#>>> imaging procedure. If you already have a split.cal file, you can
#>>> skip this step.

import glob

vislist = glob.glob('*[!_t].ms')  # match full ms, not target.ms

for myvis in vislist:

    msmd.open(myvis)
    targetspws = msmd.spwsforintent('OBSERVE_TARGET*')  
    sciencespws = []                                      
    for myspw in targetspws:                               
        if msmd.nchan(myspw)>4:
            sciencespws.append(myspw)
    sciencespws = ','.join(map(str,sciencespws))
    msmd.close()
    
    split(vis=myvis,outputvis=myvis+'.split.cal',spw=sciencespws)


########################################
# Getting a list of ms files to image

import glob

vislist=glob.glob('*.ms.split.cal')

##################################################
# Flag Bad Data [OPTIONAL]

#>>> If you have obviously bad antennas, channels, etc leftover from
#>>> the calibration, flag them here.

# Save original flags
for vis in vislist:
    flagmanager(vis=vis,
                mode='save',
                versionname='original_flags')

# Inspect the science data
fieldlist = ['3'] # list of science data fields to inspect
spwlist = ['1'] # list of science spws to inspect

# loop through science data fields and spws to inspect.

#>>> This is mainly for convenience. Note that if your field names
#>>> change between executions, you will need to create a separate loop
#>>> for each ms file.
for vis in vislist:
    for field in fieldlist:
        for spw in spwlist:
            plotms(vis=vis,xaxis='uvwave',yaxis='amp',avgtime='3e8',
                   field=field,spw=spw) 
            raw_input("push enter to continue")

            plotms(vis=vis,xaxis='chan',yaxis='amp',avgtime='3e8',
                   field=field,spw=spw) 
            raw_input("push enter to continue")

# Flag the offending data. See flagdata help for more info.
#flagdata(vis='',mode='manual',action='apply',flagbackup=False)

# If you need to restore original flags, use the following command.
#flagmanager(vis='',mode='restore',versionname='original_flags')

########################################
# Flux Equalization [OPTIONAL]

#>>> In the unlikely event you are going to equalize the fluxes between
#>>> different executions of the same SB, follow the instructions in the
#>>> Combination section at:
#>>>     https://safe.nrao.edu/wiki/bin/view/ALMA/Cycle1and2ImagingReduction#Fluxscale
#>>> Commands are provided here as a reference. If you do this step,
#>>> you will not need to do the next step (combining measurement sets
#>>> from multiple executions).

# generating the script -- REMOVE BEFORE SENDING TO PI
es.generateReducScript(['uid_FIRST-EB.ms.split.cal','uid_SECOND-EB.ms.split.cal',(etc)], step='fluxcal')

#>>> check that the commands in scriptForFluxCalibration.py is correct
#>>> and make any necessary modifications.

#>>> insert commands from scriptForFluxCalibration.py here.

###############################################################
# Combining Measurement Sets from Multiple Executions 

#>>> DO NOT DO THIS IF YOU HAVE EQUALIZED THE FLUX BETWEEN THE
#>>> DIFFERENT EXECUTIONS OF A SCHEDULING BLOCK. The flux
#>>> equalization procedure already produces a single measurement set.

# If you have multiple executions, you will want to combine the
# scheduling blocks into a single ms using concat for ease of imaging
# and self-calibration. Each execution of the scheduling block will
# generate multiple spectral windows with different sky frequencies,
# but the same rest frequency, due to the motion of the Earth. Thus,
# the resulting concatentated file will contain n spws, where n is
# (#original science spws) x (number executions).  In other words, the
# multiple spws associated with a single rest frequency will not be
# regridded to a single spectral window in the ms.

concatvis='calibrated.ms'

rmtables(concatvis)
os.system('rm -rf ' + concatvis + '.flagversions')
concat(vis=vislist,
       #forcesingleephemfield='Uranus', # uncomment this line and insert source name if imaging an ephemeris object
       concatvis=concatvis)


###################################
# Splitting off science target data

#>>> Uncomment following line for single executions
# concatvis = vislist[0]

#>>> Uncomment following line for multiple executions
# concatvis='calibrated.ms'

#>>> Doing the split.  If multiple data sets were rescaled using
#>>> scriptForFluxCalibration.py, need to get datacolumn='corrected'

sourcevis='calibrated_source.ms'
rmtables(sourcevis)
os.system('rm -rf ' + sourcevis + '.flagversions')
split(vis=concatvis,
      intent='*TARGET*', # split off the target sources
      outputvis=sourcevis,
      datacolumn='data')

###############################################################
# Regridding spectral windows [OPTIONAL]

#>>> The spws associated with a common rest frequency can be regridded to
#>>> a single spectral window during cleaning or using the cvel2
#>>> command. The NA imaging team strongly recommends the first option,
#>>> unless the lines shift too much between executions to identify an
#>>> common channel range for continuum subtraction. The code below uses
#>>> cvel to regrid multiple spws associated with a single rest frequency
#>>> into a single spw. You will want to use the same regridding
#>>> parameters later when you clean to avoid clean regridding the image
#>>> a second time.

sourcevis='calibrated_source.ms'
regridvis='calibrated_source_regrid.ms'
veltype = 'radio' # Keep set to radio. See notes in imaging section.
width = '0.23km/s' # see science goals in the OT
nchan = -1 # leave this as the default
mode='velocity' # see science goals in the OT
start='' # leave this as the default
outframe = 'bary' # velocity reference frame. see science goals in the OT.
restfreq='115.27120GHz' # rest frequency of primary line of interest. 
field = '4' # select science fields.
spw = '0,5,10' # spws associated with a single rest frequency. Do not attempt to combine spectral windows associated with different rest frequencies. This will take a long time to regrid and most likely isn't what you want.

rmtables(regridvis)
os.system('rm -rf ' + regridvis + '.flagversions')
    
cvel2(vis=sourcevis,
      field=field,
      outputvis=regridvis,
      spw=spw,
      mode=mode,
      nchan=nchan,
      width=width,
      start=start,
      restfreq=restfreq,
      outframe=outframe,
      veltype=veltype)

#>>> If you have multiple sets of spws that you wish you combine, just
#>>> repeat the above process with spw set to the other values.

############################################
# Rename and backup data set

#>>> If you haven't regridded:
# os.system('mv -i ' + sourcevis + ' ' + 'calibrated_final.ms')

#>>> If you have regridded:
# os.system('mv -i ' + regridvis + ' ' + 'calibrated_final.ms') 

# At this point you should create a backup of your final data set in
# case the ms you are working with gets corrupted by clean. 

# os.system('cp -ir calibrated_final.ms calibrated_final.ms.backup')

#>>> Please do not modify the final name of the file
#>>> ('calibrated_final.ms'). The packaging process requires a file with
#>>> this name.

############################################
# Output a listobs file

listobs(vis='calibrated_final.ms',listfile='calibrated_final.ms.listobs.txt') 
