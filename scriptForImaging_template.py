#======================================================================================#
#                        TEMPLATE IMAGING SCRIPT                                       #
# =====================================================================================#

# Updated: Thu Apr 30 13:01:12 EDT 2015

# Helpful tip: Use the commands %cpaste or %paste to copy and paste
# indented sections of code into the casa command line. 

#--------------------------------------------------------------------------------------#
#                     Data Preparation                                                 #
# -------------------------------------------------------------------------------------#

# Below are some example commands for combining your data. All of
# these commands will not be relevant for all datasets, so think about
# what would be best for your data before running any commands. For
# more information, see the NA Imaging Guide
# (https://staff.nrao.edu/wiki/bin/view/NAASC/NAImagingScripts).

# These commands should be run prior to undertaking any imaging.

# The NA Imaging team is working on generating best
# practices for this step. Suggestions are welcome!  Please send to
# akepley@nrao.edu and she'll forward them on to the NA Imaging team.

########################################
# Check CASA version

import re

if (re.search('^4.2', casadef.casa_version) or re.search('^4.3', casadef.casa_version))  == None:
 sys.exit('ERROR: PLEASE USE THE SAME VERSION OF CASA THAT YOU USED FOR GENERATING THE SCRIPT: 4.2 or 4.3')

########################################
# Getting a list of ms files to image

import glob

vislist=glob.glob('*.ms.split.cal')

########################################
# Removing pointing table

# This step removes the pointing table from the data to avoid
# a bug with mosaics in CASA 4.2.2

for vis in vislist:
    tb.open( vis + '/POINTING',
            nomodify = False)
    a = tb.rownumbers()
    tb.removerows(a)
    tb.close()


###################################
# Splitting off science target data

for vis in vislist:
    listobs(vis=vis)

    # INCLUDE LISTOBS OUTPUT FOR SCIENCE TARGET AND SPW IDS HERE.

# Doing the split
for vis in vislist:
    sourcevis=vis+'.source'
    rmtables(sourcevis)
    os.system('rm -rf ' + sourcevis + '.flagversions')
    split(vis=vis,
          intent='*TARGET*', # split off the target sources
          outputvis=sourcevis,
          datacolumn='data') # If multiple data sets were rescaled using scriptForFluxCalibration.py, need to get datacolumn='corrected'


    # Check that split worked as desired.
    listobs(vis=sourcevis) 


###############################################################
# Combining Measurement Sets from Multiple Executions [OPTIONAL]

# If you have multiple executions, you will want to combine the
# scheduling blocks into a single ms using concat for ease of imaging
# and self-calibration. Each execution of the scheduling block will
# generate multiple spectral windows with different sky frequencies,
# but the same rest frequency, due to the motion of the Earth. Thus,
# the resulting concatentated file will contain n spws, where n is
# (#original science spws) x (number executions).  In other words, the
# multiple spws associated with a single rest frequency will not be
# regridded to a single spectral window in the ms.

sourcevislist = glob.glob("*.ms.split.cal.source")
concatvis='source_calibrated_concat.ms'

rmtables(regridvis)
os.system('rm -rf ' + regridvis + '.flagversions')
concat(vis=sourcevislist,
       concatvis=concatvis)

# The spws associated with a common rest frequency can be regridded to
# a single spectral window using the clean process or using the cvel
# command. The NA imaging team strongly recommends the first option,
# unless the lines shift too much between executions to identify an
# appropriate channel range for continuum subtraction. The code below
# uses cvel to regrid multiple spws associated with a single rest
# frequency into a single spw. You will want to use the same
# regridding parameters later when you clean to avoid clean regridding
# the image a second time.

regridvis='source_calibrated_regrid.ms'
veltype = 'radio' # see science goals in the OT
width = '0.23km/s' # see science goals in the OT
nchan = -1 # leave this as the default
mode='velocity' # see science goals in the OT
start='' # leave this as the default
outframe = 'bary' # velocity reference frame. 
restfreq='115.27120GHz' # rest frequency of primary line of interest. 
field = '4' # see science goals in the OT.
spw = '0,5,10' # spws associated with a single rest frequency. Do not attempt to combine spectral windows associated with different rest frequencies. This will take a long time regrid.

rmtables(regridvis)
os.system('rm -rf ' + regridvis + '.flagversions')
    
cvel(vis=concatvis,
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

# If you have multiple sets of spws that you wish you combine, just
# repeat the above process with myspw set to the other value.

############################################
# Rename and backup data set

# If you have a single execution:
# os.system('mv -i ' + sourcevis + ' ' + 'calibrated_final.ms')

# If you have multiple executions:
# os.system('mv -i ' + regridvis + ' ' + 'calibrated_final.ms')

# At this point you should create a backup of your final data set in
# case the ms you are working with gets corrupted by clean. 

#os.system('cp -ir calibrated_final.ms calibrated_final.ms.backup')


# Please do not modify the final name of the file
# ('calibrated_final.ms'). The packaging process requires a file with
# this name.

#--------------------------------------------------------------------------------------#
#                             Imaging Template                                         #
#--------------------------------------------------------------------------------------#

# The commands below serve as a guide to best practices for imaging
# ALMA data. It does not replace careful thought on your part while
# imaging the data. You can remove or modify sections as necessary
# depending on your particular imaging case (e.g., no
# self-calibration, continuum only.) Please read the NA Imaging Guide
# (https://staff.nrao.edu/wiki/bin/view/NAASC/NAImagingScripts) for
# more information.

# Before imaging, you should use the commands the first section of
# this script to prep the data for imaging.  The commands in both file
# should be able to be run as as standard Python script. However, the
# cleaning in this script is done interactively making the final
# product somewhat dependent on the individual doing the clean --
# please clean conservatively (i.e., don't box every possible
# source). The final data products are the cleaned images (*.image),
# the primary beam corrected images (*.pbcor), and the primary beams
# (*.flux). These images should be converted to fits at the end of the
# script (see example at the end of this file).

# This script (and the associated guide) are under active
# development. Please contact Amanda Kepley (akepley@nrao.edu) if you
# have any suggested changes or find any bugs that are almost
# certainly there.

##################################################
# Identify Line-free SPWs and channels

finalvis='calibrated_final.ms' # This is your output ms from the data
                               # preparation script.

# Use plotms to identify line and continuum spectral windows
plotms(vis=finalvis, xaxis='channel', yaxis='amplitude',
       ydatacolumn='data',
       avgtime='1e8', avgscan=True, avgchannel='2', # you should only lightly average over frequency
#       avgbaseline=True, # try if you don't see anything with the time and frequency averaging
       iteraxis='spw' )

##################################################
# Create an Averaged Continuum MS

# Continuum images can be sped up considerably by averaging the data
# together to reduce overall volume.

# Project includes Continuum-only SPWs
# ----------------------------------------

# In this case, you just need to average dedicated continuum spws.

# Average channels within spws
contspws='0,1' # from plotms output
contvis='calibrated_final_cont.ms'
rmtables(contvis)
os.system('rm -rf ' + contvis + '.flagversions')
split(vis=finalvis,
      spw=contspws,
      outputvis=contvis,
      width=[128,128], # number of channels to average together. change to appropriate value for each spectral window in contspws (use listobs to find) and make sure to use the native number of channels per SPW (that is, not the number of channels left after flagging any lines)      
      datacolumn='data')   

# Complex Line Emission
# --------------------

# If you have complex line emission and no dedicated continuum
# windows, you will need to flag the line channels prior to averaging.

# Set continuum spws here based on plotms output.
contspws = '0,1,2,3'

flagmanager(vis=finalvis,mode='save',
            versionname='before_cont_flags')

# Flag the "line channels"
flagchannels='2:1201~2199,3:1201~2199' # In this example , spws 2&3 have a line between channels 1201 and
# 2199 and spectral windows 0 and 1 are line-free.

flagdata(vis=finalvis,mode='manual',
          spw=flagchannels,flagbackup=False)

# check that flags are as expected, NOTE must check reload on plotms
# gui if its still open.
plotms(vis=finalvis,yaxis='amp',xaxis='channel',
       avgchannel='2',avgtime='1e8',avgscan=True,iteraxis='spw') 

# Average the channels within spws
contvis='calibrated_final_cont.ms'
rmtables(contvis)
os.system('rm -rf ' + contvis + '.flagversions')
split(vis=finalvis,
      spw=contspws,      
      outputvis=contvis,
      width=[128,128,3840,3840], # number of channels to average together. change to appropriate value for each spectral window in contspws (use listobs to find) and make sure to use the native number of channels per SPW (that is, not the number of channels left after flagging any lines)
      datacolumn='data')

# Note: There is a bug in split that does not average the data
# properly if the width is set to a value larger than the number of
# channels in an SPW. Specifying the width of each spw (as done above)
# is necessary for producing properly weighted data.

# Restore the flags
flagmanager(vis=finalvis,mode='restore',
            versionname='before_cont_flags')

# Inspect continuum for any problems
plotms(vis=contvis,xaxis='uvdist',yaxis='amp',coloraxis='spw')

# #############################################
# Image Parameters

# You're now ready to image. Review the science goals in the OT and
# set the relevant imaging parameters below. 

# source parameters
# ------------------

field='0' # science field(s). For a mosaic, select all mosaic fields. DO NOT LEAVE BLANK ('') OR YOU WILL TRIGGER A BUG IN CLEAN THAT WILL PUT THE WRONG COORDINATE SYSTEM ON YOUR FINAL IMAGE.
# imagermode='csclean' # uncomment if single field
# imagermode='mosaic' # uncomment if mosaic
# phasecenter=3 # uncomment and set to field number for phase
                # center. Note lack of ''.  Use the weblog to
                # determine which pointing to use. Remember that the
                # field ids for each pointing will be re-numbered
                # after your initial split. You can also specify the
                # phase center using coordinates, e.g.,
                # phasecenter='J2000 19h30m00 -40d00m00'

# image parameters.
# ----------------

# Generally, you want 5-8 cells (i.e., pixels) across the narrowest
# part of the beam, which is 206265.0/(longest baseline in
# wavelengths).  You can use plotms with xaxis='uvwave' and
# yaxis='amp' to see what the longest baseline is. Divide by five to
# eight to get your cell size. It's better to error on the side of
# slightly too many cells per beam than too few. Once you have made an
# image, please re-assess the cell size based on the beam of the
# image.

# To determine the image size (i.e., the imsize parameter), first need
# to figure out whether or not the ms is a mosaic by either looking
# out the output from listobs or checking the spatial setup in the
# OT. For single fields, an imsize equal to the size of the primary
# beam is usually sufficient. The ALMA 12m primary beam in arcsec
# scales as 6300 / nu[GHz] and the ALMA 7m primary beam in arcsec
# scales as 10608 / nu[GHz]. However, if there is significant point
# source and/or extended emission (beyond the edges of your initial
# images, you should increase the imsize to incorporate more
# emission. For mosaics, you can get the imsize from the spatial tab
# of the OT. If you're imaging a mosaic, pad the imsize substantially
# to avoid artifacts.

cell='1arcsec' # cell size for imaging.
imsize = [128,128] # size of image in pixels. 

# imaging control
# ----------------

# The cleaning below is done interactively, so niter and threshold can
# be controlled within clean. 

weighting = 'briggs'
robust=0.5
niter=1000
threshold = '0.0mJy'

#############################################
# Imaging the Continuuum

# If necessary, run the following commands to get rid of older clean
# data.

#clearcal(vis=contvis)
#delmod(vis=contvis)
         
contimagename = 'calibrated_final_cont_image'

for ext in ['.flux','.image','.mask','.model','.pbcor','.psf','.residual','.flux.pbcoverage']:
    rmtables(contimagename+ext)

clean(vis=contvis,
      imagename=contimagename,
      field=field,
#      phasecenter=phasecenter, # uncomment if mosaic.      
      mode='mfs',
      psfmode='clark',
      imsize = imsize, 
      cell= cell, 
      weighting = weighting, 
      robust = robust,
      niter = niter, 
      threshold = threshold, 
      interactive = True,
      imagermode = imagermode)

# If interactively cleaning (interactive=True), then note number of
# iterations at which you stop for the PI. This number will help the
# PI replicate the delivered images.

# Note RMS for PI. 

# If you'd like to redo your clean, but don't want to make a new mask
# use the following commands to save your original mask. This is an optional step.
#contmaskname = 'cont.mask'
##rmtables(contmaskname) # if you want to delete the old mask
#os.system('cp -ir ' + contimagename + '.mask ' + contmaskname)

##############################################
# Self-calibration on the continuum [OPTIONAL]

# If the source continuum is bright, you can attempt to self-calibrate
# on it.  The example here obtains solutions from the scan time to
# down to times as short as per integration. Depending on the source,
# you may not be able to find solution on timescales that short and
# may need to adjust the solint parameter.

# set these for self-calibration solutions
refant = 'DV09' # reference antenna. Choose one that's in the array. The tasks plotants and listobs can tell you what antennas are in the array.
spwmap = [0,0,0] # mapping self-calibration solutions to individual spectral windows. Generally an array of n zeroes, where n is the number of spectral windows in the data sets.

# shallow clean on the continuum

for ext in ['.flux','.image','.mask','.model','.pbcor','.psf','.residual','.flux.pbcoverage']:
    rmtables(contimagename + '_p0'+ ext)
    

clean(vis=contvis,
      imagename=contimagename + '_p0',
      field=field,
#      phasecenter=phasecenter, # uncomment if mosaic.      
      mode='mfs',
      psfmode='clark',
      imsize = imsize, 
      cell= cell, 
      weighting = weighting, 
      robust=robust,
      niter=niter, 
      threshold=threshold, 
      interactive=True,
      imagermode=imagermode)

# Note number of iterations performed.

# per scan solution
rmtables('pcal1')
gaincal(vis=contvis,
        caltable='pcal1',
        field=field,
        gaintype='T',
        refant=refant, 
        calmode='p',
        combine='spw', 
        solint='inf',
        minsnr=3.0,
        minblperant=6)

# Check the solution
plotcal(caltable='pcal1',
        xaxis='time',
        yaxis='phase',
        timerange='',
        iteration='antenna',
        subplot=421,
        plotrange=[0,0,-180,180])

# apply the calibration to the data for next round of imaging
applycal(vis=contvis,
         field=field,
         spwmap=spwmap, 
         gaintable=['pcal1'],
         gainfield='',
         calwt=F, 
         flagbackup=F)

# clean deeper
for ext in ['.flux','.image','.mask','.model','.pbcor','.psf','.residual','.flux.pbcoverage']:
    rmtables(contimagename + '_p1'+ ext)

clean(vis=contvis,
      field=field,
#      phasecenter=phasecenter, # uncomment if mosaic.      
      imagename=contimagename + '_p1',
      mode='mfs',
      psfmode='clark',
      imsize = imsize, 
      cell= cell, 
      weighting = weighting, 
      robust=robust,
      niter=niter, 
      threshold=threshold, 
      interactive=True,
      imagermode=imagermode)

# Note number of iterations performed.

# shorter solution
rmtables('pcal2')
gaincal(vis=contvis,
        field=field,
        caltable='pcal2',
        gaintype='T',
        refant=refant, 
        calmode='p',
        combine='spw', 
        solint='30.25s', # solint=30.25s gets you five 12m integrations, while solint=50.5s gets you five 7m integration
        minsnr=3.0,
        minblperant=6)

# Check the solution
plotcal(caltable='pcal2',
        xaxis='time',
        yaxis='phase',
        timerange='',
        iteration='antenna',
        subplot=421,
        plotrange=[0,0,-180,180])

# apply the calibration to the data for next round of imaging
applycal(vis=contvis,
         spwmap=spwmap, 
         field=field,
         gaintable=['pcal2'],
         gainfield='',
         calwt=F, 
         flagbackup=F)

# clean deeper
for ext in ['.flux','.image','.mask','.model','.pbcor','.psf','.residual','.flux.pbcoverage']:
    rmtables(contimagename + '_p2'+ ext)

clean(vis=contvis,
      imagename=contimagename + '_p2',
      field=field,
#      phasecenter=phasecenter, # uncomment if mosaic.            
      mode='mfs',
      psfmode='clark',
      imsize = imsize, 
      cell= cell, 
      weighting = weighting, 
      robust=robust,
      niter=niter, 
      threshold=threshold, 
      interactive=True,
      imagermode=imagermode)

# Note number of iterations performed.

# shorter solution
rmtables('pcal3')
gaincal(vis=contvis,
        field=field,
        caltable='pcal3',
        gaintype='T',
        refant=refant, 
        calmode='p',
        combine='spw', 
        solint='int',
        minsnr=3.0,
        minblperant=6)

# Check the solution
plotcal(caltable='pcal3',
        xaxis='time',
        yaxis='phase',
        timerange='',
        iteration='antenna',
        subplot=421,
        plotrange=[0,0,-180,180])

# apply the calibration to the data for next round of imaging
applycal(vis=contvis,
         spwmap=spwmap,
         field=field,
         gaintable=['pcal3'],
         gainfield='',
         calwt=F, 
         flagbackup=F)

# do the amplitude self-calibration.
for ext in ['.flux','.image','.mask','.model','.pbcor','.psf','.residual','.flux.pbcoverage']:
    rmtables(contimagename + '_p3'+ ext)

clean(vis=contvis,
      imagename=contimagename + '_p3',
      field=field,
#      phasecenter=phasecenter, # uncomment if mosaic.            
      mode='mfs',
      psfmode='clark',
      imsize = imsize, 
      cell= cell, 
      weighting = weighting, 
      robust=robust,
      niter=niter, 
      threshold=threshold, 
      interactive=True,
      imagermode=imagermode)

# Note number of iterations performed.

rmtables('apcal')
gaincal(vis=contvis,
        field=field,
        caltable='apcal',
        gaintype='T',
        refant=refant,
        calmode='ap',
        combine='spw',
        solint='inf',
        minsnr=3.0,
        minblperant=6,
#        uvrange='>50m', # may need to use to exclude extended emission
        gaintable='pcal3',
        spwmap=spwmap,
        solnorm=True)

plotcal(caltable='apcal',
        xaxis='time',
        yaxis='amp',
        timerange='',
        iteration='antenna',
        subplot=421,
        plotrange=[0,0,0.2,1.8])

applycal(vis=contvis,
         spwmap=[spwmap,spwmap], # select which spws to apply the solutions for each table
         field=field,
         gaintable=['pcal3','apcal'],
         gainfield='',
         calwt=F,
         flagbackup=F)

# Make amplitude and phase self-calibrated image.
for ext in ['.flux','.image','.mask','.model','.pbcor','.psf','.residual','.flux.pbcoverage']:
    rmtables(contimagename + '_ap'+ ext)

clean(vis=contvis,
      imagename=contimagename + '_ap',
      field=field, 
#      phasecenter=phasecenter, # uncomment if mosaic.      
      mode='mfs',
      psfmode='clark',
      imsize = imsize, 
      cell= cell, 
      weighting = weighting, 
      robust=robust,
      niter=niter, 
      threshold=threshold, 
      interactive=True,
      imagermode=imagermode)

# Note final RMS and number of clean iterations. Compare the RMS to
# the RMS from the earlier, pre-selfcal image.

# Save results of self-cal in a new ms
split(vis=contvis,
      outputvis=contvis+'.selfcal',
      datacolumn='corrected')

########################################
# Continuum Subtraction for Line Imaging

# If you have observations that include both line and strong (>3 sigma
# per final line image channel) continuum emission, you need to
# subtract the continuum from the line data. You should not continuum
# subtract if the line of interest is in absorption.

fitspw = '0,1,2:0~1200;1500~3839,3:0~1200;1500~3839' # line-free channel for fitting continuum
linespw = '2,3' # line spectral windows. You can subtract the continuum from multiple spectral line windows at once.

uvcontsub(vis=finalvis,
          spw=linespw, # spw to do continuum subtraction on
          fitspw=fitspw, # select spws to fit continuum. exclude regions with strong lines.
          combine='spw', 
          solint='int',
          fitorder=1,
          want_cont=False) # This value should not be changed.

# NOTE: Imaging the continuum produced by uvcontsub with
# want_cont=True will lead to extremely poor continuum images because
# of bandwidth smearing effects. For imaging the continuum, you should
# always create a line-free continuum data set using the process
# outlined above.

linevis = finalvis+'.contsub'

#########################################################
# Apply continuum self-calibration to line data [OPTIONAL]

spwmap_line = [0] # Mapping self-calibration solution to the individual line spectral windows.
applycal(vis=linevis,
         spwmap=[spwmap_line, spwmap_line], # select which spws to apply the solutions for each table
         field=field,
         gaintable=['pcal3','apcal'],
         gainfield='',
         calwt=F,
         flagbackup=F)

# Save results of self-cal in a new ms and reset the image name.
split(vis=linevis,
      outputvis=linevis+'.selfcal',
      datacolumn='corrected')
linevis=linevis+'.selfcal'


##############################################
# Image line emission [REPEAT AS NECESSARY]

# If you did an mstransform/cvel, use the same velocity parameters in
# the clean that you did for the regridding. If you did not do an
# mstransform and have multiple executions of a scheduling block,
# select the spws with the same rest frequency using the spw parameter
# (currently commented out below). DO NOT INCLUDE SPWS WITH DIFFERENT
# REST FREQUENCIES IN THE SAME RUN OF CLEAN: THEY WILL SLOW DOWN
# IMAGING CONSIDERABLY.

# If necessary, run the following commands to get rid of older clean
# data.

#clearcal(vis=linevis)
#delmod(vis=linevis)

# velocity parameters
# -------------------

lineimagename = 'source_calibrated_line_image' # name of line image

start='-100km/s' # start velocity. See science goals for appropriate value.
width='2km/s' # velocity width. See science goals.
nchan = 100  # number of channels. See science goals for appopriate value.
outframe='bary' # velocity reference frame. See science goals.
veltype='radio' # velocity type. See note below.
restfreq='115.27120GHz' # Typically the rest frequency of the line of
                        # interest. If the source has a significant
                        # redshift (z>0.2), use the observed sky
                        # frequency (nu_rest/(1+z)) instead of the
                        # rest frequency of the
                        # line.

# spw='1' # uncomment and replace with appropriate spw if necessary.

# To specify a spws from multiple executions, use
#       import numpy as np
#       spw = str.join(',',map(str,np.arange(0,n,nspw)))
#
# where n is the total number of windows x executions and nspw is the
# number of spectral windows per execution. Note that the spectral
# windows need to have the same order in all data sets for this code
# to work. Add a constant offset (i.e., +1,+2,+3) to the array
# generated by np.arange to get the other sets of windows.

# Note on veltype: We recommend keeping veltype set to radio,
# regardless of the velocity frame listed the object in the OT. If the
# sensitivity is defined using a velocity width, then the 'radio'
# definition of the velocity frame is used regardless of the velocity
# definition in the "source parameters" tab of the OT.

for ext in ['.flux','.image','.mask','.model','.pbcor','.psf','.residual','.flux.pbcoverage']:
    rmtables(lineimagename + ext)

clean(vis=linevis,
      imagename=lineimagename, 
      field=field,
#      spw=spw,
#      phasecenter=phasecenter, # uncomment if mosaic.      
      mode='velocity',
      start=start,
      width=width,
      nchan=nchan, 
      outframe=outframe, 
      veltype=veltype, 
      restfreq=restfreq, 
      niter=niter,  
      threshold=threshold, 
      interactive=True,
      cell=cell,
      imsize=imsize, 
      weighting=weighting, 
      robust=robust,
      imagermode=imagermode)

# If interactively cleaning (interactive=True), then note number of
# iterations at which you stop for the PI. This number will help the
# PI replicate the delivered images.

# If you'd like to redo your clean, but don't want to make a new mask
# use the following commands to save your original mask. This is an
# optional step.
# linemaskname = 'line.mask'
## rmtables(linemaskname) # uncomment if you want to overwrite the mask.
# os.system('cp -ir ' + lineimagename + '.mask ' + linemaskname)

##############################################
# Apply a primary beam correction

import glob

myimages = glob.glob("*.image")

rmtables('*.pbcor')
for image in myimages:
    impbcor(imagename=image, pbimage=image.replace('.image','.flux'), outfile = image.replace('.image','.pbcor'))

##############################################
# Export the images

import glob

myimages = glob.glob("*.image")
for image in myimages:
    exportfits(imagename=image, fitsimage=image+'.fits',overwrite=True)

myimages = glob.glob("*.pbcor")
for image in myimages:
    exportfits(imagename=image, fitsimage=image+'.fits',overwrite=True)

myimages = glob.glob("*.flux")
for image in myimages:
    exportfits(imagename=image, fitsimage=image+'.fits',overwrite=True) 

##############################################
# Analysis

# For examples of how to get started analyzing your data, see 
#     http://casaguides.nrao.edu/index.php?title=TWHydraBand7_Imaging_4.2
