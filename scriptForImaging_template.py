#>>> =====================================================================================#
#>>>                        TEMPLATE IMAGING SCRIPT                                       #
#>>> =====================================================================================#
#>>>
#>>> Updated: Wed Apr  7 09:57:35 EDT 2021

#>>> Lines beginning with '#>>>' are instructions to the data imager
#>>> and will be removed from the script delivered to the PI. If you
#>>> would like to include a comment that will be passed to the PI,
#>>> begin the line with a single '#', i.e., standard python comment
#>>> syntax.  Helpful tip: Use the commands %cpaste or %paste to copy
#>>> and paste indented sections of code into the casa command line.

#>>> The commands below serve as a guide to best practices for imaging
#>>> ALMA data. It does not replace careful thought on your part while
#>>> imaging the data. You can remove or modify sections as necessary
#>>> depending on your particular imaging case (e.g., no
#>>> self-calibration, continuum only.) Please read the NA Imaging
#>>> Guide
#>>> (https://staff.nrao.edu/wiki/bin/view/NAASC/NAImagingScripts) for
#>>> more information.  Before imaging, you should use the commands
#>>> the first section of this script to prep the data for imaging.
#>>> The commands in both sections should be able to be run as as
#>>> standard Python script. However, the cleaning in this script is
#>>> done interactively making the final product somewhat dependent on
#>>> the individual doing the clean -- please clean conservatively
#>>> (i.e., don't box every possible source). The final data products
#>>> are the primary beam corrected images (*.pbcor), and the primary
#>>> beams (*.pb). These images should be converted to fits at the end
#>>> of the script (see example at the end of this file).  This script
#>>> (and the associated guide) are under active development. Please
#>>> contact Amanda Kepley (akepley@nrao.edu) if you have any
#>>> suggested changes or find any bugs that are almost certainly
#>>> there.

# This script has been tested for CASA 6.1.1-15.


########################################
# Check CASA version

import re

try:
    import casalith
except:
    print("Script requires CASA 6.0 or greater")


if casalith.compare_version("<",[6,1,1,15]):
    print("Please use CASA version greater than or equal to 6.1.1-15 with this script")


##################################################
# Create an Averaged Continuum MS

#>>> Continuum images can be sped up considerably by averaging the data
#>>> together to reduce overall volume. Since the sensitivity of a
#>>> continuum image depends on its bandwidth, continuum images are
#>>> typically made by including as much bandwidth as possible in the
#>>> data while excluding any line emission. The following plotms command
#>>> pages through the spectral windows in a project allowing you to
#>>> identify channel ranges within spectral windows that do not include
#>>> *strong* line emission. You will form a continuum image by averaging
#>>> the line-free spws and/or channel ranges within spws. In most cases,
#>>> you will not need to create an image to select line channels,
#>>> although you can suggest this to the PI as a possible path for
#>>> future exploration in the README file for cases where there is
#>>> wide-spread line emission.
#>>>
#>>> For a project with continuum target sensitivities, it is worth
#>>> checking the OT to see what continuum bandwidth the PI was
#>>> anticipating. In many cases, the continuum-only windows will be
#>>> specified in the OT, in general these have the broadest bandwidths
#>>> (~2GHz) with a small number of channels (128).  However, other
#>>> windows may be combined with these designated continuum windows to
#>>> increase the continuum sensitivity. In general, it is not necessary
#>>> to include narrow spectral windows (<250MHz) in the continuum image.

finalvis='calibrated_final.ms' # This is your output ms from the data
                               # preparation script.

# Use plotms to identify line and continuum spectral windows.
#>>> If you have a project with multiple fields, you will want to run
#>>> the following plotms command separately for each source. If the
#>>> spectra for each field are significantly different from each other,
#>>> it may be necessary to make separate average continuum  and
#>>> continuum-subtracted measurement sets for each field.
plotms(vis=finalvis, xaxis='channel', yaxis='amplitude',
       ydatacolumn='data',
       avgtime='1e8', avgscan=True, avgchannel='1', 
       iteraxis='spw' )


#>>> Note that when you average channels in plotms, it displays
#>>> the "bin" number rather than the average channel number of each
#>>> bin. 

#>>> If you don't see any obvious lines in the above plot, you may to try
#>>> to set avgbaseline=True with uvrange (e.g., <100m). Limiting the
#>>> uvrange to the short baselines greatly improves the visibility of
#>>> lines with extended emission.

#>>> If you have multiple sources, the line channel ranges may be
#>>> different for different sources. Thus you would need to repeat the
#>>> process below for each source.


# Set spws to be used to form continuum
contspws = '0,1,2,3'

# If you have complex line emission and no dedicated continuum
# windows, you will need to flag the line channels prior to averaging.
flagmanager(vis=finalvis,mode='save',
            versionname='before_cont_flags')

initweights(vis=finalvis,wtmode='weight',dowtsp=True)

# Flag the "line channels"
flagchannels='2:1201~2199,3:1201~2199' # In this example , spws 2&3 have a line between channels 1201 and 2199 and spectral windows 0 and 1 are line-free.


flagdata(vis=finalvis,mode='manual',
          spw=flagchannels,flagbackup=False)

# check that flags are as expected, NOTE must check reload on plotms
# gui if its still open.
plotms(vis=finalvis,yaxis='amp',xaxis='channel',
       avgchannel='1',avgtime='1e8',avgscan=True,iteraxis='spw') 

# Average the channels within spws
contvis='calibrated_final_cont.ms'
rmtables(contvis)
os.system('rm -rf ' + contvis + '.flagversions')

#>>> Note that to mitigate bandwidth smearing, please keep the width
#>>> of averaged channels less than 125MHz in Band 3, 4, and 6, and 250MHz
#>>> in Band 7 for both TDM and FDM modes. For example, for a 2GHz TDM window
#>>> with 15.625 MHz channels, this means that the maximum width parameter
#>>> should be 8 channels for Bands 3, 4, and 6 and 16 channels for Band 7.
#>>> This is especially important for any long baseline data. These limits
#>>> have been designed to have minimize the reduction of the peak flux to
#>>> 95%. See the "for continuum" header for more information on the imaging
#>>> wiki for more infomration.

#>>> Note that in CASA 5.1, split2 is now split. Previously split2 was
#>>> needed to deal correctly with channelized weights.
split(vis=finalvis,
     spw=contspws,      
     outputvis=contvis,
      width=[256,8,8,8], # number of channels to average together. The final channel width should be less than 125MHz in Bands 3, 4, and 6 and 250MHz in Band 7.
     datacolumn='data')


# Check the weights. You will need to change antenna and field to
# appropriate values
plotms(vis=contvis, yaxis='wtsp',xaxis='freq',spw='',antenna='DA42',field='0')

# If you flagged any line channels, restore the previous flags
flagmanager(vis=finalvis,mode='restore',
            versionname='before_cont_flags')

# Inspect continuum for any problems
plotms(vis=contvis,xaxis='uvdist',yaxis='amp',coloraxis='spw')

# #############################################
# Image Parameters

#>>> You're now ready to image. Review the science goals in the OT and
#>>> set the relevant imaging parameters below. 

# source parameters
# ------------------

field='0' # science field(s). For a mosaic, select all mosaic fields. DO NOT LEAVE BLANK ('') OR YOU WILL POTENTIALLY TRIGGER A BUG IN CLEAN THAT WILL PUT THE WRONG COORDINATE SYSTEM ON YOUR FINAL IMAGE.
# gridder='standard' # uncomment if single field 
# gridder='mosaic' # uncomment if mosaic or if combining one 7m and one 12m pointing.
# phasecenter=3 # uncomment and set to field number for phase
                # center. Note lack of ''.  Use the weblog to
                # determine which pointing to use. Remember that the
                # field ids for each pointing will be re-numbered
                # after your initial split. You can also specify the
                # phase center using coordinates, e.g.,
                # phasecenter='J2000 19h30m00 -40d00m00'.
# phasecenter = 'TRACKFIELD' # If imaging an ephemeris object (planet, etc), the phasecenter needs to be TRACKFIELD, not a field number as above.


# image parameters.
# ----------------

#>>> Generally, you want 5-8 cells (i.e., pixels) across the narrowest
#>>> part of the beam. You can estimate the beam size using the following
#>>> equation: 206265.0/(longest baseline in wavelengths).  To determine
#>>> the longest baseline, use plotms with xaxis='uvwave' and
#>>> yaxis='amp'. Divide the estimated beam size by five to eight to get
#>>> your cell size. It's better to error on the side of slightly too
#>>> many cells per beam than too few. Once you have made an image,
#>>> please re-assess the cell size based on the beam of the image. You can
#>>> check your cell size using  au.pickCellSize('calibrated_final.ms'). Note
#>>> however, that this routine does not take into account the projection of
#>>> the baseline onto the sky, so the plotms method described above is overall
#>>> more accurate.

#>>> To determine the image size (i.e., the imsize parameter), first you
#>>> need to figure out whether the ms is a mosaic by either looking out
#>>> the output from listobs/vishead or checking the spatial setup in the OT. For
#>>> single fields, an imsize equal to the size of the primary beam is
#>>> usually sufficient. The ALMA 12m primary beam in arcsec scales as
#>>> 6300 / nu[GHz] and the ALMA 7m primary beam in arcsec scales as
#>>> 10608 / nu[GHz], where nu[GHz] is the sky frequency. However, if
#>>> there is significant point source and/or extended emission beyond
#>>> the edges of your initial images, you should increase the imsize to
#>>> incorporate more emission. For mosaics, you can get the imsize from
#>>> the spatial tab of the OT. The parameters "p length" and "q length"
#>>> specify the dimensions of the mosaic. If you're imaging a mosaic,
#>>> pad the imsize substantially to avoid artifacts. Note that the imsize
#>>> parameter is in PIXELS, not arcsec, so you will need to divide the image size
#>>> in arcsec by the pixel size to determine a value for imsize.

#>>> Note that you can check your image size using 
#>>> au.pickCellSize('calibrated_final.ms', imsize=True). This task
#>>> now works both mosaics and single fields, but has not been tested
#>>> extensively on mosaics. Please report any large issues to
#>>> Todd Hunter. Note that au.pickCellSize does not take
#>>> into account the projection of the baselines, so the plotms
#>>> method is more accurate.

cell='1arcsec' # cell size for imaging.
imsize = [128,128] # size of image in pixels.

# velocity parameters
# -------------------

outframe='lsrk' # velocity reference frame. 
veltype='radio' # velocity type. 

#>>> Note on veltype: For quality assurance purposes, we recommend keeping veltype
#>>> set to radio, regardless of the velocity frame listed the object in the OT.
#>>> If the sensitivity in the OT is defined using a velocity width, then the 'radio'
#>>> definition of the velocity frame is used regardless of the velocity
#>>> definition in the "source parameters" tab of the OT.

# imaging control
# ----------------

# The cleaning below is done interactively, so niter and threshold can
# be controlled within clean. 

weighting = 'briggs'
robust=0.5
niter=1000
threshold = '0.0mJy'

#>>> Guidelines for setting robust:

#>>> Robust < 0.0 is not recommended for mosaics with poor-uv
#>>> coverage. Using values of robust less than or equal to 0.0 will
#>>> lead to major artifacts in the images including uneven noise
#>>> across the image.

#>>> If you are uv-tapering the data, you should set robust=2 (natural
#>>> weighting) to avoid upweighting points that are going to be
#>>> downweighted by uv-taper.

#############################################
# Imaging the Continuuum

# Set the ms and continuum image name.
contvis = 'calibrated_final_cont.ms'         

#>>> Generate the relevant image name and copy and paste imagename for PI

#>>> The spwmap parameter renumbers the images to match the archival
#>>> spectral windows, which aren't renumbered, unlike the manual
#>>> imaging spectral windows, which are renumbered by split in the
#>>> imaging prep script. It is defined similarly to other spwmap
#>>> parameters. For example, to map spw (e.g., 0,1,2,3) in
#>>> *.split.cal to their original values (e.g., 17, 19, 21, 23), you
#>>> would set spwmap=[17,19,21,23]. The sciencespws variable was
#>>> created in the scriptForImagingPrep.py in the first step. You can
#>>> also do a listobs on the original ms to get the spectral windows,
#>>> e.g.,
#>>> listobs(vis='uid___A002_Xc3412f_X53ff.ms',intent='OBSERVE_TARGET*',spw='*FULL_RES*')

#>>>  aU.genImageName(vis=contvis,spw=map(int,contspws.split(',')),field=int(field.split('~')[0]),imtype='mfs',targettype='sci',stokes='I',mous='',modtext='manual',spwmap=map(int,sciencespws.split(',')))
contimagename = '' 

# If necessary, run the following commands to get rid of older clean
# data.

#clearcal(vis=contvis)
#delmod(vis=contvis)

for ext in ['.image','.mask','.model','.image.pbcor','.psf','.residual','.pb','.sumwt']:
    rmtables(contimagename+ext)

#>>> If you're going be be imaging with nterms>1, then you also need
#>>> to removed the *.tt0, and *.tt1 images in additional to those
#>>> listed above.

#>>> If the fractional bandwidth for the aggregate continuum is
#>>> greater than 10%, set deconvolver='mtmfs' to use multi-term,
#>>> multi-frequency synthesis. This algorithm takes into account the
#>>> spatial spectral index variations in an image.  Note that only
#>>> ALMA Band 3 and the lower end of Band 4 can have fractional
#>>> bandwidths of greater than 10% and only when both sidebands are
#>>> employed.

tclean(vis=contvis,
       imagename=contimagename,
       field=field,
       #  phasecenter=phasecenter, # uncomment if mosaic or imaging an ephemeris object     
       # mosweight = True, # uncomment if mosaic
       specmode='mfs',
       deconvolver='hogbom', 
       # Uncomment the below to image with nterms>1 when the fractional bandwidth is greater than 10%.
       #deconvolver='mtmfs',
       #nterms=2,
       imsize = imsize, 
       cell= cell, 
       weighting = weighting,
       robust = robust,
       niter = niter, 
       threshold = threshold,
       interactive = True,
       gridder = gridder,
       pbcor = True,
       usepointing=False)
       
#>>> If interactively cleaning (interactive=True), then note number of
#>>> iterations at which you stop for the PI. This number will help
#>>> the PI replicate the delivered images. Do not clean empty
#>>> images. Just click the red X to stop the interactive and note the
#>>> RMS.

#>>> Note RMS for PI. 

# If you'd like to redo your clean, but don't want to make a new mask
# use the following commands to save your original mask. This is an optional step.
#contmaskname = 'cont.mask'
##rmtables(contmaskname) # if you want to delete the old mask
#os.system('cp -ir ' + contimagename + '.mask ' + contmaskname)

##############################################
# Self-calibration on the continuum [OPTIONAL]

#>>> Self-calibration solutions can be determined when a source exhibits
#>>> a strong continuum emission, preferably near the phase
#>>> center. Self-calibration can be attempted in cases where the
#>>> expected rms is not reached on the continuum (for projects where the
#>>> sensitivity is defined for the continuum) or the line data (for
#>>> projects where the sensitivity is defined for the line data). It
#>>> should not be attempted on 'partial' datasets (ACA and _TC datasets),
#>>> and, in the interest of reducing the time required to image, is not
#>>> recommended for datasets which do meet the rms requirement

#>>> The example here obtains solutions from the scan time to
#>>> down to times as short as per integration. Depending on the source,
#>>> you may not be able to find solution on timescales that short and
#>>> may need to adjust the solint parameter.

contvis = 'calibrated_final_cont.ms'         
contimagename = '' # Grab from continuum imaging step above if needed.

refant = 'DV09' # reference antenna.

#>>> Choose a reference antenna that's in the array. The tasks plotants
#>>> and listobs/vishead can tell you what antennas are in the array. For
#>>> data sets with multiple executions, you will want to choose an antenna
#>>> that's present in all the executions. The task au.commonAntennas()
#>>> can help with this.

#>>> Indicate the spectral window mapping below. The spwmap map
#>>> variable is a list that consists of n entries where n is the
#>>> number of spectral windows. The value of each entry tells you
#>>> which solution to apply to the indicated spectral window. For a
#>>> single execution, you would apply the calibration from spw 0 to
#>>> all spws since you are combining all spws in the solution below,
#>>> so spwmap=[0,0,0,0]. For multiple executions, you want to apply
#>>> the solution for each execution to itself. For example, if you had 4
#>>> spectral windows in a data set and two executions resulting in 8
#>>> total spectral windows, you would want to apply the solutions for
#>>> the first execution to itself and the solution to the second
#>>> execution to itself, so spwmap=[0,0,0,0,4,4,4,4]

spwmap = [0,0,0,0] # mapping self-calibration solutions to individual spectral windows.

# save initial flags in case you don't like the final
# self-calibration. The task applycal will flag data that doesn't have
# solutions.
flagmanager(vis=contvis,mode='save',versionname='before_selfcal',merge='replace')

# Get rid of any models that might be hanging around in the image header
delmod(vis=contvis,otf=True,scr=True)

# If you are re-doing your self-cal, uncomment the next line to reset
# your corrected data column back to its original state and get rid of
# the old model. You can check the contents of the model and corrected
# data columns by plotting them using plotms. For example, 
# plotms(vis=contvis, xaxis='uvwave', yaxis='amplitude', ydatacolumn='model',field=field)

# clearcal(vis=contvis)
# delmod(vis=contvis,otf=True,scr=True)

# shallow clean on the continuum

for ext in ['.image','.mask','.model','.image.pbcor','.psf','.residual','.pb','.sumwt']:
    rmtables(contimagename + '_p0'+ ext)

tclean(vis=contvis,
       imagename=contimagename + '_p0',
       field=field,
       #phasecenter=phasecenter, # uncomment if mosaic or imaging an ephemeris object
       # mosweight = True, # uncomment if mosaic
       specmode='mfs',
       deconvolver='hogbom',
       # Uncomment the below to image with nterms>1.
       #deconvolver='mtmfs',
       #nterms=2,
       imsize = imsize, 
       cell= cell, 
       weighting = weighting, 
       robust=robust,
       niter=niter, 
       threshold=threshold, 
       interactive=True,
       gridder=gridder,
       savemodel='modelcolumn',
       usepointing=False)

#>>> Note number of iterations performed.

#>>> Note: before proceeding, you should verify that TCLEAN saved the MODEL 
#>>> column. If it did, you will see a message like
#>>> INFO .... ------ Predict Model ------
#>>> INFO ... Saving model column
#>>> if you don't see this in the CASA logger, you should call TCLEAN again 
#>>> with niter=0, calcpsf=False, calcres=False to populate the modelcolumn

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

#>>> If many of the above many solutions are flagged, consider setting
#>>> minsnr=1.5 and comparing the solutions. For low (<~500) dynamic
#>>> range cases, including a bit more random noise in the solution
#>>> has only a small effect on the image.

# Check the solution
plotms(vis='pcal1',
       xaxis='time',
       yaxis='phase',
       iteraxis='antenna',
       plotrange=[0,0,-180,180])

# apply the calibration to the data for next round of imaging
applycal(vis=contvis,
         field=field,
         spwmap=spwmap, 
         gaintable=['pcal1'],
         gainfield='',
         calwt=False, 
         flagbackup=False,
         interp='linearperobs')

# clean deeper
for ext in ['.image','.mask','.model','.image.pbcor','.psf','.residual','.pb','.sumwt']:
    rmtables(contimagename + '_p1'+ ext)

tclean(vis=contvis,
       imagename=contimagename + '_p1',
       field=field,
       # phasecenter=phasecenter, # uncomment if mosaic or imaging an ephemeris object
       # mosweight = True, # uncomment if mosaic
       specmode='mfs',
       deconvolver='hogbom',
       # Uncomment the below to image with nterms>1.
       #deconvolver='mtmfs',
       #nterms=2,
       imsize = imsize, 
       cell= cell, 
       weighting = weighting, 
       robust=robust,
       niter=niter, 
       threshold=threshold, 
       interactive=True,
       gridder=gridder,
       #pbcor = True, #if final image
       savemodel='modelcolumn',
       usepointing=False)

#>>> Note number of iterations performed.


#>>> Note: before proceeding, you should verify that TCLEAN saved the MODEL 
#>>> column. If it did, you will see a message like
#>>> INFO .... ------ Predict Model ------
#>>> INFO ... Saving model column
#>>> if you don't see this in the CASA logger, you should call TCLEAN again 
#>>> with niter=0, calcpsf=False, calcres=False to populate the modelcolumn

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
plotms(vis='pcal2',
       xaxis='time',
       yaxis='phase',
       iteraxis='antenna',
       plotrange=[0,0,-180,180])

# apply the calibration to the data for next round of imaging
applycal(vis=contvis,
         spwmap=spwmap, 
         field=field,
         gaintable=['pcal2'],
         gainfield='',
         calwt=False, 
         flagbackup=False,
         interp='linearperobs')

# clean deeper
for ext in ['.image','.mask','.model','.image.pbcor','.psf','.residual','.pb','.sumwt']:
    rmtables(contimagename + '_p2'+ ext)

tclean(vis=contvis,
       imagename=contimagename + '_p2',
       field=field,
       # phasecenter=phasecenter, # uncomment if mosaic or imaging an ephemeris object
       # mosweight = True, # uncomment if mosaic
       specmode='mfs',
       deconvolver='hogbom',
       # Uncomment the below to image with nterms>1.
       #deconvolver='mtmfs',
       #nterms=2,
       imsize = imsize, 
       cell= cell, 
       weighting = weighting, 
       robust=robust,
       niter=niter, 
       threshold=threshold, 
       interactive=True,
       gridder=gridder,
       #pbcor = True, #if final image
       savemodel='modelcolumn',
       usepointing=False)

#>>> Note number of iterations performed.

#>>> Note: before proceeding, you should verify that TCLEAN saved the MODEL 
#>>> column. If it did, you will see a message like
#>>> INFO .... ------ Predict Model ------
#>>> INFO ... Saving model column
#>>> if you don't see this in the CASA logger, you should call TCLEAN again 
#>>> with niter=0, calcpsf=False, calcres=False to populate the modelcolumn

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
plotms(vis='pcal3',
       xaxis='time',
       yaxis='phase',
       iteraxis='antenna',
       plotrange=[0,0,-180,180])

# apply the calibration to the data for next round of imaging
applycal(vis=contvis,
         spwmap=spwmap,
         field=field,
         gaintable=['pcal3'],
         gainfield='',
         calwt=False, 
         flagbackup=False,
         interp='linearperobs')

# do the amplitude self-calibration.
for ext in ['.image','.mask','.model','.image.pbcor','.psf','.residual','.pb','.sumwt']:
    rmtables(contimagename + '_p3'+ ext)

tclean(vis=contvis,
       imagename=contimagename + '_p3',
       field=field,
       # phasecenter=phasecenter, # uncomment if mosaic or imaging an ephemeris object
       # mosweight = True, # uncomment if mosaic
       specmode='mfs',
       deconvolver='hogbom',
       # Uncomment the below to image with nterms>1.
       #deconvolver='mtmfs',
       #nterms=2,
       imsize = imsize, 
       cell= cell, 
       weighting = weighting, 
       robust=robust,
       niter=niter, 
       threshold=threshold, 
       interactive=True,
       gridder=gridder,
       #pbcor = True, #if final image
       savemodel='modelcolumn',
       usepointing=False)


#>>> Note number of iterations performed.

#>>> Note: before proceeding, you should verify that TCLEAN saved the MODEL 
#>>> column. If it did, you will see a message like
#>>> INFO .... ------ Predict Model ------
#>>> INFO ... Saving model column
#>>> if you don't see this in the CASA logger, you should call TCLEAN again 
#>>> with niter=0, calcpsf=False, calcres=False to populate the modelcolumn


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

plotms(vis='apcal',
       xaxis='time',
       yaxis='amp',
       iteraxis='antenna',
       plotrange=[0,0,0.2,1.8])

applycal(vis=contvis,
         spwmap=[spwmap,spwmap], # select which spws to apply the solutions for each table
         field=field,
         gaintable=['pcal3','apcal'],
         gainfield='',
         calwt=False,
         flagbackup=False,
         interp=['linearperobs','linearperobs'])

# Make amplitude and phase self-calibrated image.
for ext in ['.image','.mask','.model','.image.pbcor','.psf','.residual','.pb','.sumwt']:
    rmtables(contimagename + '_ap'+ ext)


tclean(vis=contvis,
       imagename=contimagename + '_ap',
       field=field,
       # phasecenter=phasecenter, # uncomment if mosaic or imaging an ephemeris object
       # mosweight = True, # uncomment if mosaic
       specmode='mfs',
       deconvolver='hogbom',
       # Uncomment the below to image with nterms>1.
       #deconvolver='mtmfs',
       #nterms=2,
       imsize = imsize, 
       cell= cell, 
       weighting = weighting, 
       robust=robust,
       niter=niter, 
       threshold=threshold, 
       interactive=True,
       gridder=gridder,
       savemodel='modelcolumn',
       pbcor=True,
       usepointing=False) # apply the primary beam correction since this is the last image.

#>>> Note final RMS and number of clean iterations. Compare the RMS to
#>>> the RMS from the earlier, pre-selfcal image.

# Save results of self-cal in a new ms
split(vis=contvis,
      outputvis=contvis+'.selfcal',
      datacolumn='corrected')

# reset the corrected data column in the  ms to the original calibration.

#>>> This can also be used to return your ms to it's original
#>>> pre-self-cal state if you are unhappy with your self-calibration.
clearcal(vis=contvis)

#>>> The applycal task will automatically flag data without good
#>>> gaincal solutions. If you are unhappy with your self-cal and wish to
#>>> return the flags to their original state, run the following command
#>>> flagmanager(vis=contvis, mode='restore',versionname='before_selfcal')


########################################
# Continuum Subtraction for Line Imaging

#>>> If you have observations that include both line and strong (>3 sigma
#>>> per final line image channel) continuum emission, you need to
#>>> subtract the continuum from the line data. You should not continuum
#>>> subtract if the line of interest is in absorption.

#>>> You can use au.invertChannelRanges(flagchannels,vis=finalvis) to
#>>> get the fitspw below. You will need to insert any continuum spws
#>>> that weren't included in flagchannels. For example, if your continuum
#>>> spws are '0,1,2' and flagchannels='1:260~500', au.invertChannelRanges will return
#>>> '1:0~259,1:501~3839'. The fitspw parameter should be '0,1:0~259,1:501~3839,2'
#>>> Make sure to cut and paste the output in fitspw below since PIs don't have
#>>> analysisUtilities by default.

fitspw = '2:0~1200;1500~3839,3:0~1200;1500~3839' # *line-free* channels for fitting continuum
linespw = '2,3' # line spectral windows. You can subtract the continuum from multiple spectral line windows at once. The linespw must be in the fitspw unless combine='spw'

finalvis='calibrated_final.ms'

uvcontsub(vis=finalvis,
          spw=linespw, # spw to do continuum subtraction on
          fitspw=fitspw, # regions without lines.
          excludechans=False, # fit the regions in fitspw
          #combine='spw', uncomment if there are no line-free channels in the line spectral window.  
          solint='int',
          fitorder=1,
          want_cont=False) # This value should not be changed.

#>>> Note that the continuum subtraction is done for each field in 
#>>> turn. However, if the fields have different line-free channels, you
#>>> will need to do the continuum subtraction separately for each field.

# NOTE: Imaging the continuum produced by uvcontsub with
# want_cont=True will lead to extremely poor continuum images because
# of bandwidth smearing effects. For imaging the continuum, you should
# always create a line-free continuum data set using the process
# outlined above.

#########################################################
# Apply continuum self-calibration to line data [OPTIONAL]

# uncomment one  of the following
# linevis = finalvis+'.contsub' # if continuum subtracted
# linevis = finalvis  #  if not continuum subtracted

# save original flags in case you don't like the self-cal
flagmanager(vis=linevis,mode='save',versionname='before_selfcal',merge='replace')

spwmap_line = [0] # Mapping self-calibration solution to the individual line spectral windows.
applycal(vis=linevis,
         spwmap=[spwmap_line, spwmap_line], # entering the appropriate spwmap_line value for each spw in the input dataset
         field=field,
         gaintable=['pcal3','apcal'],
         gainfield='',
         calwt=False,
         flagbackup=False,
         interp=['linearperobs','linearperobs'])

# Save results of self-cal in a new ms and reset the image name.
split(vis=linevis,
      outputvis=linevis+'.selfcal',
      datacolumn='corrected')

# reset the corrected data column in the  ms to the original calibration
#>>> This can also be used to return your ms to it's original
#>>> pre-self-cal state if you are unhappy with your self-calibration.
clearcal(linevis)

#>>> The applycal task will automatically flag data without good
#>>> gaincal solutions. If you are unhappy with your self-cal and wish to
#>>> return the flags to their original state, run the following command
#>>> flagmanager(vis=linevis, mode='restore',versionname='before_selfcal')

linevis=linevis+'.selfcal'

##############################################
# Image line emission [REPEAT AS NECESSARY]

#>>> If you did an mstransform/cvel, use the same velocity parameters in
#>>> the clean that you did for the regridding. If you did not do an
#>>> mstransform and have multiple executions of a scheduling block,
#>>> select the spws with the same rest frequency using the spw parameter
#>>> (currently commented out below). DO NOT INCLUDE SPWS WITH DIFFERENT
#>>> REST FREQUENCIES IN THE SAME RUN OF CLEAN: THEY WILL SLOW DOWN
#>>> IMAGING CONSIDERABLY.

finalvis = 'calibrated_final.ms'
# linevis = finalvis # uncomment if you neither continuum subtracted nor self-calibrated your data.
# linevis = finalvis + '.contsub' # uncomment if continuum subtracted
# linevis = finalvis + '.contsub.selfcal' # uncommment if both continuum subtracted and self-calibrated
# linevis = finalvis + '.selfcal' # uncomment if just self-calibrated (no continuum subtraction)



restfreq='115.27120GHz' # Typically the rest frequency of the line of
                        # interest. If the source has a significant
                        # redshift (z>0.2), use the observed sky
                        # frequency (nu_rest/(1+z)) instead of the
                        # rest frequency of the
                        # line.

# spw='1' # uncomment and replace with appropriate spw 

#>>> To specify a spws from multiple executions that had not been regridded using cvel, use
#>>>       import numpy as np
#>>>       spw = str.join(',',map(str,np.arange(0,n,nspw)))
#>>>
#>>> where n is the total number of windows x executions and nspw is the
#>>> number of spectral windows per execution. Note that the spectral
#>>> windows need to have the same order in all data sets for this code
#>>> to work. Add a constant offset (i.e., +1,+2,+3) to the array
#>>> generated by np.arange to get the other sets of windows.

#>>> Automatically generate image name for PI and paste info below
#>>>  aU.genImageName(vis=finalvis,spw=map(int,spw.split(',')),field=int(field.split('~')[0]),imtype='cube',targettype='sci',stokes='I',mous='',modtext='manual',spwmap=map(int,sciencespws.split(','))

#>>>  If you don't have the variable sciencespws already set, you can
#>>>  determine it via a listobs on the original ms:
#>>>     listobs(vis='uid___A002_Xc3412f_X53ff.ms',intent='OBSERVE_TARGET*',spw='*FULL_RES*')
#>>>  Note that sciencespws needs to be a list of integers.

lineimagename =  ''

start='-100km/s' # start velocity. See science goals for appropriate value.
width='2km/s' # velocity width. See science goals.
nchan = 100  # number of channels. See science goals for appropriate value.

# If necessary, run the following commands to get rid of older clean
# data.

#clearcal(vis=linevis)
#delmod(vis=linevis)

for ext in ['.image','.mask','.model','.image.pbcor','.psf','.residual','.pb','.sumwt']:
    rmtables(lineimagename + ext)

tclean(vis=linevis,
       imagename=lineimagename, 
       field=field,
       spw=spw,
       # phasecenter=phasecenter, # uncomment if mosaic or imaging an ephemeris object   
       # mosweight = True, # uncomment if mosaic      
       specmode='cube', # comment this if observing an ephemeris source
       # specmode='cubesource', #uncomment this line if observing an ephemeris source
       # perchanweightdensity=False # uncomment if you are running in CASA >= 5.5.0. 
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
       gridder=gridder,
       pbcor=True,
       restoringbeam='common',
       chanchunks=-1, # break up large cubes automatically so that you don't run out of memory.
       usepointing=False) 

#>>> If interactively cleaning (interactive=True), then note number of
#>>> iterations at which you stop for the PI. This number will help the
#>>> PI replicate the delivered images. Do not clean empty
#>>> images. Just click the red X to stop the interactive and note the
#>>> RMS.

# If you'd like to redo your clean, but don't want to make a new mask
# use the following commands to save your original mask. This is an
# optional step.
# linemaskname = 'line.mask'
## rmtables(linemaskname) # uncomment if you want to overwrite the mask.
# os.system('cp -ir ' + lineimagename + '.mask ' + linemaskname)

##############################################
# Export the images

import glob

myimages = glob.glob("*.pbcor")
for image in myimages:
    exportfits(imagename=image, fitsimage=image+'.fits',overwrite=True)

myimages = glob.glob("*.pb")
for image in myimages:
    exportfits(imagename=image, fitsimage=image+'.fits',overwrite=True) 

##############################################
# Create Diagnostic PNGs

os.system("rm -rf *.png")
mycontimages = glob.glob("*mfs*manual.image")
for cimage in mycontimages:
    mymax=imstat(cimage)['max'][0]
    mymin=-0.1*mymax
    outimage = cimage+'.png'
    os.system('rm -rf '+outimage)
    imview(raster={'file':cimage,'range':[mymin,mymax]},out=outimage)

mylineimages = glob.glob("*cube*manual.image")
for limage in mylineimages:
    mom8=limage+'.mom8'
    os.system("rm -rf "+mom8)
    immoments(limage,moments=[8],outfile=mom8)
    mymax=imstat(mom8)['max'][0]
    mymin=-0.1*mymax
    os.system("rm -rf "+mom8+".png")
    imview(raster={'file':mom8,'range':[mymin,mymax]},out=mom8+'.png')


##############################################
# Analysis

# For examples of how to get started analyzing your data, see
#     https://casaguides.nrao.edu/index.php/TWHydraBand7_Imaging_4.3
#     
