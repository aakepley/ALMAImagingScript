#>>> ======================================================================================#
#>>>                        TEMPLATE IMAGING SCRIPT                                       #
#>>> =====================================================================================#
#>>>
#>>> Updated: Thu Feb  4 13:26:39 EST 2016

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
#>>>                             Imaging Template                                         #
#>>>--------------------------------------------------------------------------------------#
#>>>
#>>> The commands below serve as a guide to best practices for imaging
#>>> ALMA data. It does not replace careful thought on your part while
#>>> imaging the data. You can remove or modify sections as necessary
#>>> depending on your particular imaging case (e.g., no
#>>> self-calibration, continuum only.) Please read the NA Imaging Guide
#>>> (https://staff.nrao.edu/wiki/bin/view/NAASC/NAImagingScripts) for
#>>> more information.
#>>>
#>>> Before imaging, you should use the commands the first section of
#>>> this script to prep the data for imaging.  The commands in both
#>>> sections should be able to be run as as standard Python
#>>> script. However, the cleaning in this script is done interactively
#>>> making the final product somewhat dependent on the individual doing
#>>> the clean -- please clean conservatively (i.e., don't box every
#>>> possible source). The final data products are the cleaned images
#>>> (*.image), the primary beam corrected images (*.pbcor), and the
#>>> primary beams (*.flux). These images should be converted to fits at
#>>> the end of the script (see example at the end of this file).
#>>>
#>>> This script (and the associated guide) are under active
#>>> development. Please contact Amanda Kepley (akepley@nrao.edu) if you
#>>> have any suggested changes or find any bugs that are almost
#>>> certainly there.

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


#>>> In CASA 4.4 and higher, the behavior of the avgchannel parameter
#>>> has changed. Now when you plot binned channels, plotms displays
#>>> the "bin" number rather than the average channel number of each
#>>> bin. Amanda is trying to get this behavior changed back to
#>>> something more sensible

#>>> If you don't see any obvious lines in the above plot, you may to try
#>>> to set avgbaseline=True with uvrange (e.g., <100m). Limiting the
#>>> uvrange to the short baselines greatly improves the visibility of
#>>> lines with extended emission.


# Set spws to be used to form continuum
contspws = '0,1,2,3'

# If you have complex line emission and no dedicated continuum
# windows, you will need to flag the line channels prior to averaging.
flagmanager(vis=finalvis,mode='save',
            versionname='before_cont_flags')

## UNCOMMENT ONLY IF YOU ARE USING CASA 4.4 OR HIGHER TO IMAGE THE DATA
## (CURRENTLY ONLY MANUAL REDUCTIONS)
# initweights(vis=finalvis,wtmode='weight',dowtsp=True)

# Flag the "line channels"
flagchannels='2:1201~2199,3:1201~2199' # In this example , spws 2&3 have a line between channels 1201 and
# 2199 and spectral windows 0 and 1 are line-free.

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
#>>> with 16.625 MHz channels, this means that the maximum width parameter
#>>> should be 8 channels for Bands 3, 4, and 6 and 16 channels for Band 7.
#>>> This is especially important for any long baseline data.

# IF YOU ARE USING CASA VERSION 4.4 AND ABOVE TO IMAGE, UNCOMMENT THE FOLLOWING. DELETE IF NOT APPROPRRIATE.
# split2(vis=finalvis,
#      spw=contspws,      
#      outputvis=contvis,
#      width=[128,128,3840,3840], # number of channels to average together. The final channel width should be less than 125MHz in Bands 3, 4, and 6 and 250MHz in Band 7.
#      datacolumn='data')

# IF YOU ARE USING CASA VERSION 4.3 AND BELOW TO IMAGE, UNCOMMENT THE FOLLOWING. DELETE IF NOT APPROPRIATE.
# split(vis=finalvis,
#       spw=contspws,      
#       outputvis=contvis,
#       width=[128,128,3840,3840], # number of channels to average together. The final channel width should be less than 125MHz in Bands 3, 4, and 6 and 250MHz in Band 7.
#       datacolumn='data')

# Note: There is a bug in split (but not split2) that does not average
# the data properly if the width is set to a value larger than the
# number of channels in an SPW. Specifying the width of each spw (as
# done above) is necessary for producing properly weighted data.

# IN CASA 4.4 and above, you should check the weights. You will need to change antenna and field to appropriate values
# plotms(vis=contvis, yaxis='wtsp',xaxis='freq',spw='',antenna='DA42',field='0')

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

outframe='bary' # velocity reference frame. See science goals.
veltype='radio' # velocity type. See note below.

#>>> Note on veltype: We recommend keeping veltype set to radio,
#>>> regardless of the velocity frame listed the object in the OT. If the
#>>> sensitivity is defined using a velocity width, then the 'radio'
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

#############################################
# Imaging the Continuuum

# Set the ms and continuum image name.
contvis = 'calibrated_final_cont.ms'         
contimagename = 'calibrated_final_cont'

# If necessary, run the following commands to get rid of older clean
# data.

#clearcal(vis=contvis)
#delmod(vis=contvis)

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
#>>> should not be tempted on 'partial' datasets (ACA and _TC datasets),
#>>> and, in the interest of reducing the time required to image, is not
#>>> recommended for datasets which do meet the rms requirement

#>>> The example here obtains solutions from the scan time to
#>>> down to times as short as per integration. Depending on the source,
#>>> you may not be able to find solution on timescales that short and
#>>> may need to adjust the solint parameter.

contvis = 'calibrated_final_cont.ms'         
contimagename = 'calibrated_final_cont'

refant = 'DV09' # reference antenna.

#>>> Choose a reference antenna that's in the array. The tasks plotants
#>>> and listobs/vishead can tell you what antennas are in the array. For
#>>> data sets with multiple executions, you will want to choose an antenna
#>>> that's present in all the executions. The task au.commonAntennas()
#>>> can help with this.

spwmap = [0,0,0] # mapping self-calibration solutions to individual spectral windows. Generally an array of n zeroes, where n is the number of spectral windows in the data sets.

# save initial flags in case you don't like the final
# self-calibration. The task applycal will flag data that doesn't have
# solutions.
flagmanager(vis=contvis,mode='save',versionname='before_selfcal',merge='replace')

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
      usescratch=True, # needed for 4.3 and 4.4 (and maybe 4.5)
      imagermode=imagermode)

#>>> Note number of iterations performed.

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
         flagbackup=F,
         interp='linearperobs')

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
      usescratch=True, # needed for 4.3 and 4.4 (and maybe 4.5)
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
         flagbackup=F,
         interp='linearperobs')

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
      usescratch=True, # needed for 4.3 and 4.4 (and maybe 4.5)
      imagermode=imagermode)

#>>> Note number of iterations performed.

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
         flagbackup=F,
         interp='linearperobs')

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
      usescratch=True, # needed for 4.3 and 4.4 (and maybe 4.5)
      imagermode=imagermode)

#>>> Note number of iterations performed.

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
         flagbackup=F,
         interp='linearperobs')

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
      usescratch=True, # needed for 4.3 and 4.4 (and maybe 4.5)
      imagermode=imagermode)

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

fitspw = '0,1,2:0~1200;1500~3839,3:0~1200;1500~3839' # line-free channel for fitting continuum
linespw = '2,3' # line spectral windows. You can subtract the continuum from multiple spectral line windows at once.

finalvis='calibrated_final.ms'

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

linevis = finalvis+'.contsub'

# save original flags in case you don't like the self-cal
flagmanager(vis=linevis,mode='save',versionname='before_selfcal',merge='replace')

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

sourcename ='n253' # name of source
linename = 'CO10' # name of transition (see science goals in OT for name) 
lineimagename = sourcename+'_'+linename # name of line image

restfreq='115.27120GHz' # Typically the rest frequency of the line of
                        # interest. If the source has a significant
                        # redshift (z>0.2), use the observed sky
                        # frequency (nu_rest/(1+z)) instead of the
                        # rest frequency of the
                        # line.

# spw='1' # uncomment and replace with appropriate spw if necessary.

start='-100km/s' # start velocity. See science goals for appropriate value.
width='2km/s' # velocity width. See science goals.
nchan = 100  # number of channels. See science goals for appropriate value.

#>>> To specify a spws from multiple executions that had not been regridded using cvel, use
#>>>       import numpy as np
#>>>       spw = str.join(',',map(str,np.arange(0,n,nspw)))
#>>>
#>>> where n is the total number of windows x executions and nspw is the
#>>> number of spectral windows per execution. Note that the spectral
#>>> windows need to have the same order in all data sets for this code
#>>> to work. Add a constant offset (i.e., +1,+2,+3) to the array
#>>> generated by np.arange to get the other sets of windows.

# If necessary, run the following commands to get rid of older clean
# data.

#clearcal(vis=linevis)
#delmod(vis=linevis)

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
# Apply a primary beam correction

import glob

myimages = glob.glob("*.image")

rmtables('*.pbcor')
for image in myimages:
    pbimage = image.rsplit('.',1)[0]+'.flux'
    outfile = image.rsplit('.',1)[0]+'.pbcor'
    impbcor(imagename=image, pbimage=pbimage, outfile = outfile)

##############################################
# Export the images

import glob

myimages = glob.glob("*.pbcor")
for image in myimages:
    exportfits(imagename=image, fitsimage=image+'.fits',overwrite=True)

myimages = glob.glob("*.flux")
for image in myimages:
    exportfits(imagename=image, fitsimage=image+'.fits',overwrite=True) 

##############################################
# Create Diagnostic PNGs

#>>> The following code has not be extensively tested. Please let
#>>> Amanda Kepley know if you find problems.

os.system("rm -rf *.png")
mycontimages = glob.glob("calibrated*.image")
for cimage in mycontimages:
    max=imstat(cimage)['max'][0]
    min=-0.1*max
    outimage = cimage+'.png'
    os.system('rm -rf '+outimage)
    imview(raster={'file':cimage,'range':[min,max]},out=outimage)


# this will have to be run for each sourcename
sourcename='' # insert source here, if it isn't already set
mylineimages = glob.glob(sourcename+"*.image")
for limage in mylineimages:
    rms=imstat(limage,chans='1')['rms'][0]
    mom8=limage+'.mom8'
    os.system("rm -rf "+mom8)
    immoments(limage,moments=[8],outfile=mom8)
    max=imstat(mom8)['max'][0]
    min=-0.1*max
    os.system("rm "+mom8+".png")
    imview(raster={'file':mom8,'range':[min,max]},out=mom8+'.png')


##############################################
# Analysis

# For examples of how to get started analyzing your data, see 
#     http://casaguides.nrao.edu/index.php?title=TWHydraBand7_Imaging_4.2
