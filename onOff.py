#!/usr/bin/env python

# Built-in packages
import argparse

# Local packages
from interface import wideToDesign
from interface import Flags


def getOptions():
    """Function to pull in arguments"""
    description = """"""
    parser = argparse.ArgumentParser(description=description)

    group1 = parser.add_argument_group(title='Standard input', description='Standard input for SECIM tools.')
    group1.add_argument("--input", dest="fname", action='store', required=True, help="Input dataset in wide format.")
    group1.add_argument("--design", dest="dname", action='store', required=True, help="Design file.")
    group1.add_argument("--ID", dest="uniqID", action='store', required=True, help="Name of the column with unique identifiers.")
    group1.add_argument("--output", dest="output", action='store', required=True, help="Output path for the created flag file.")
    group1.add_argument("--group", dest="group", action='store', required=True, default=None, help="Add the option to separate sample IDs by treatement name. ")

    group2 = parser.add_argument_group(title='Optional input', description='Optional input for On/Off tool.')
    group2.add_argument("--cutoff", dest="cutoff", action='store', default=30000, type=int, required=False, help="Cutoff to use for which values to flag. This defaults to 30,000")

    args = parser.parse_args()

    return(args)


def main(args):

    # Import data
    dat = wideToDesign(args.fname, args.dname, args.uniqID)

    df_onOffFlags = Flags(index=dat.wide.index)

    # Iterate through each group to add flags for if a group has over half of
    # its data above the cutoff
    for title, group in dat.design.groupby(args.group):
        # Create mask of current frame containing True/False values if the
        # values are greater than the cutoff
        mask = (dat.wide[group.index] > args.cutoff)

        # Convert the mean column to a boolean
        meanOn = mask.mean(axis=1)

        # Add mean column of boolean values to flags
        df_onOffFlags.addColumn(column='flag_' + title + '_on', mask=meanOn > 0.5)

    # flag_met_on column
    maskFlagMetOn = df_onOffFlags.df_flags.any(axis=1)
    df_onOffFlags.addColumn('flag_met_on', maskFlagMetOn)

    # flag_met_all_on column
    maskFlagMetAllOn = df_onOffFlags.df_flags.all(axis=1)
    df_onOffFlags.addColumn('flag_met_all_on', maskFlagMetAllOn)

    df_onOffFlags.df_flags.to_csv(args.output, sep="\t")

if __name__ == "__main__":

    # Command line options
    args = getOptions()

    main(args)

