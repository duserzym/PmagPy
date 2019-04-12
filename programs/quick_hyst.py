#!/usr/bin/env python
from pmag_env import set_env
import pmagpy.contribution_builder as cb
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag
import sys
import os
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")


def main():
    """
    NAME
        quick_hyst.py

    DESCRIPTION
        makes plots of hysteresis data

    SYNTAX
        quick_hyst.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input file, default is measurements.txt
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    pltspec = ""
    verbose = pmagplotlib.verbose
    dir_path = pmag.get_named_arg('-WD', '.')
    dir_path = os.path.realpath(dir_path)
    meas_file = pmag.get_named_arg('-f', 'measurements.txt')
    fmt = pmag.get_named_arg('-fmt', 'png')
    save_plots = False
    interactive = True
    if '-sav' in args:
        verbose = False
        save_plots = True
        interactive = False
    if '-spc' in args:
        ind = args.index("-spc")
        pltspec = args[ind+1]
        verbose = False
        save_plots = True
    quick_hyst(dir_path, meas_file, save_plots,
               interactive, fmt, pltspec, verbose)


def quick_hyst(dir_path=".", meas_file="measurements.txt", save_plots=True,
               interactive=False, fmt="png", specimen="", verbose=True):
    """
    makes specimen plots of hysteresis data

    Parameters
    ----------
    dir_path : str, default "."
        input directory
    meas_file : str, default "measurements.txt"
        name of MagIC measurement file
    save_plots : bool, default True
        save figures
    interactive : bool, default False
        if True, interactively plot and display
        (this is best used on the command line only)
    fmt : str, default "svg"
        format for figures, ["svg", "jpg", "pdf", "png"]
    specimen : str, default ""
        specific specimen to plot
    verbose : bool, default True
        if True, print more verbose output

    Returns
    ---------
    Tuple : (True or False indicating if conversion was sucessful, output file name(s) written)
    """

    con = cb.Contribution(dir_path, read_tables=['measurements'],
                          custom_filenames={'measurements': meas_file})
    # get as much name data as possible (used for naming plots)
    if 'measurements' not in con.tables:
        print("-W- No measurement file found")
        return False, []
    con.propagate_location_to_measurements()

    if 'measurements' not in con.tables:
        print(main.__doc__)
        print('bad file')
        return False, []
    meas_container = con.tables['measurements']
    #meas_df = meas_container.df

    #
    # initialize some variables
    # define figure numbers for hyst,deltaM,DdeltaM curves
    saved = []
    HystRecs = []
    HDD = {}
    HDD['hyst'] = 1
    pmagplotlib.plot_init(HDD['hyst'], 5, 5)
    #
    # get list of unique experiment names and specimen names
    #
    sids = []
    hyst_data = meas_container.get_records_for_code('LP-HYS')
    #experiment_names = hyst_data['experiment_name'].unique()
    if not len(hyst_data):
        print("-W- No hysteresis data found")
        return False, []
    if 'specimen' not in hyst_data.columns:
        print('-W- No specimen names in measurements data, cannot complete quick_hyst.py')
        return False, []
    sids = hyst_data['specimen'].unique()

    # if 'treat_temp' is provided, use that value, otherwise assume 300
    hyst_data['treat_temp'].where(
        hyst_data['treat_temp'].notnull(), '300', inplace=True)
    # start at first specimen, or at provided specimen ('-spc')
    k = 0
    if specimen:
        try:
            print(sids)
            k = list(sids).index(specimen)
        except ValueError:
            print('-W- No specimen named: {}.'.format(specimen))
            print('-W- Please provide a valid specimen name')
            return False, []
    intlist = ['magn_moment', 'magn_volume', 'magn_mass']

    while k < len(sids):
        locname, site, sample, synth = '', '', '', ''
        s = sids[k]
        if verbose:
            print(s, k + 1, 'out of ', len(sids))
        # B, M for hysteresis, Bdcd,Mdcd for irm-dcd data
        B, M = [], []
        # get all measurements for this specimen
        spec = hyst_data[hyst_data['specimen'] == s]
        # get names
        if 'location' in spec:
            locname = spec['location'].iloc[0]
        if 'site' in spec:
            site = spec['sample'].iloc[0]
        if 'sample' in spec:
            sample = spec['sample'].iloc[0]
        # get all records with non-blank values in any intlist column
        # find intensity data
        for int_column in intlist:
            if int_column in spec.columns:
                int_col = int_column
                break
        meas_data = spec[spec[int_column].notnull()]
        if len(meas_data) == 0:
            break
        #
        c = ['k-', 'b-', 'c-', 'g-', 'm-', 'r-', 'y-']
        cnum = 0
        Temps = []
        xlab, ylab, title = '', '', ''
        Temps = meas_data['treat_temp'].unique()
        for t in Temps:
            print('working on t: ', t)
            t_data = meas_data[meas_data['treat_temp'] == t]
            m = int_col
            B = t_data['meas_field_dc'].astype(float).values
            M = t_data[m].astype(float).values
            # now plot the hysteresis curve(s)
            #
            if len(B) > 0:
                B = numpy.array(B)
                M = numpy.array(M)
                if t == Temps[-1]:
                    xlab = 'Field (T)'
                    ylab = m
                    title = 'Hysteresis: ' + s
                if t == Temps[0]:
                    pmagplotlib.clearFIG(HDD['hyst'])
                pmagplotlib.plot_xy(
                    HDD['hyst'], B, M, sym=c[cnum], xlab=xlab, ylab=ylab, title=title)
                pmagplotlib.plot_xy(HDD['hyst'], [
                                    1.1*B.min(), 1.1*B.max()], [0, 0], sym='k-', xlab=xlab, ylab=ylab, title=title)
                pmagplotlib.plot_xy(HDD['hyst'], [0, 0], [
                                    1.1*M.min(), 1.1*M.max()], sym='k-', xlab=xlab, ylab=ylab, title=title)
                if not save_plots and not set_env.IS_WIN:
                    pmagplotlib.draw_figs(HDD)
                cnum += 1
                if cnum == len(c):
                    cnum = 0
  #
        files = {}
        if save_plots:
            if specimen != "":
                s = specimen
            for key in list(HDD.keys()):
                if pmagplotlib.isServer:
                    if synth == '':
                        files[key] = "LO:_"+locname+'_SI:_'+site + \
                            '_SA:_'+sample+'_SP:_'+s+'_TY:_'+key+'_.'+fmt
                    else:
                        files[key] = 'SY:_'+synth+'_TY:_'+key+'_.'+fmt
                else:
                    if synth == '':
                        filename = ''
                        for item in [locname, site, sample, s, key]:
                            if item:
                                item = item.replace(' ', '_')
                                filename += item + '_'
                        if filename.endswith('_'):
                            filename = filename[:-1]
                        filename += ".{}".format(fmt)
                        files[key] = filename
                    else:
                        files[key] = "{}_{}.{}".format(synth, key, fmt)

            pmagplotlib.save_plots(HDD, files)
            saved.extend([key for key in files])
            if specimen:
                return True, saved
        if interactive:
            pmagplotlib.draw_figs(HDD)
            ans = input(
                "S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue\n ")
            if ans == "a":
                files = {}
                for key in list(HDD.keys()):
                    if pmagplotlib.isServer:  # use server plot naming convention
                        locname = locname if locname else ""
                        site = site if site else ""
                        sample = sample if sample else ""
                        files[key] = "LO:_"+locname+'_SI:_'+site + \
                            '_SA:_'+sample+'_SP:_'+s+'_TY:_'+key+'_.'+fmt
                    else:  # use more readable plot naming convention
                        filename = ''
                        for item in [locname, site, sample, s, key]:
                            if item:
                                item = item.replace(' ', '_')
                                filename += item + '_'
                        if filename.endswith('_'):
                            filename = filename[:-1]
                        filename += ".{}".format(fmt)
                        files[key] = filename

                pmagplotlib.save_plots(HDD, files)
                saved.extend([key for key in files])
            if ans == '':
                k += 1
            if ans == "p":
                del HystRecs[-1]
                k -= 1
            if ans == 'q':
                print("Good bye")
                return True, []
            if ans == 's':
                keepon = 1
                specimen = input(
                    'Enter desired specimen name (or first part there of): ')
                while keepon == 1:
                    try:
                        k = list(sids).index(specimen)
                        keepon = 0
                    except ValueError:
                        tmplist = []
                        for qq in range(len(sids)):
                            if specimen in sids[qq]:
                                tmplist.append(sids[qq])
                        print(specimen, " not found, but this was: ")
                        print(tmplist)
                        specimen = input('Select one or try again\n ')
                        k = list(sids).index(specimen)
        else:
            k += 1
        if not B:
            if verbose:
                print('skipping this one - no hysteresis data')
            k += 1
    return True, saved


if __name__ == "__main__":
    main()
