#!/usr/bin/env python
# Built-in packages
import re
import sys

# Add-on packages
import numpy as np
import pandas as pd


class wideToDesign:
    """ Class to handle generic data in a wide format with an associated design file. """
    def __init__(self, wide, design, uniqID, group=False, runOrder=False, anno=False, clean_string=True, infer_sampleID=True, keepSample=True, logger=None):
        """ Import and set-up data.

        Import data both wide formated data and a design file. Set-up basic
        attributes.

        :Arguments:
            wide (TSV): A table in wide format with compounds/genes as rows and
                samples as columns.

                Name     sample1   sample2   sample3
                ------------------------------------
                one      10        20        10
                two      10        20        10

            design (TSV): A table relating samples ('sampleID') to groups or
                treatments.

                sampleID   group1  group2
                -------------------------
                sample1    g1      t1
                sample2    g1      t1
                sample3    g1      t1

            uniqID (str): The name of the unique identifier column in 'wide'
                (i.e. The column with compound/gene names).

            group (str): The name of column names in 'design' that give
                group information. For example: treatment

            clean_string (bool): If True remove special characters from strings
                in dataset.

            infer_sampleID (bool): If True infer "sampleID" from different capitalizations.

            anno (list): A list of additional annotations that can be used to group
                items.

        :Returns:
            **Attribute**

            self.uniqID (str): The name of the unique identifier column in 'wide'
                (i.e. The column with compound/gene names).

            self.wide (pd.DataFrame): A wide formatted table with compound/gene
                as row and sample as columns.

            self.sampleIDs (list): A list of sampleIDs. These will correspond
                to columns in self.wide.

            self.design (pd.DataFrame): A table relating sampleID to groups.

            self.group (list): A list of column names in self.design that give
                group information. For example: treatment, tissue

            anno (list): A list of additional annotations that can be used to group
                items.

            self.levels (list): A list of levels in self.group. For example:
                trt1, tr2, control.

        """
        # Setting logger
        if logger is None:
            self.logger = False
        else:
            self.logger = logger

        # Saving original str
        self.origString = dict()

        # Import wide formatted data file
        try:
            self.uniqID = uniqID
            self.wide = pd.read_table(wide)
            if clean_string:
                self.wide[self.uniqID] = self.wide[self.uniqID].apply(lambda x: self._cleanStr(str(x)))
                self.wide.rename(columns= lambda x:self._cleanStr(x),inplace=True)

            # Make sure index is a string and not numeric
            self.wide[self.uniqID] = self.wide[self.uniqID].astype(str)

            # Set index to uniqID column
            self.wide.set_index(self.uniqID, inplace=True)
                
        except:
            if self.logger:
                self.logger.error("Please make sure that your data file has a column called '{0}'.".format(uniqID))
            else:
                print ("Please make sure that your data file has a column called '{0}'.".format(uniqID))
            raise ValueError

        # Import design file
        try:
            self.design = pd.read_table(design)

            # This part of the script allows the user to use any capitalization of "sampleID"
            # ie. "sample Id" would be converted to "sampleID".
            # If you want to accept only the exact capitalization turn infer_sampleID to Fake
            if infer_sampleID:
                renamed = {column:re.sub(r"[s|S][a|A][m|M][p|P][l|L][e\E][\s?|_?][I|i][d|D]","sampleID",column) for column in self.design.columns}
                self.design.rename(columns=renamed,inplace=True)
                if self.logger:
                    self.logger.info("Infering 'sampleID' from data. This will accept different capitalizations of the word")
                else:
                    print ("Infering 'sampleID' from data. This will accept different capitalizations of the word")

            # Make sure index is a string and not numeric
            self.design['sampleID'] = self.design['sampleID'].astype(str)
            self.design.set_index('sampleID', inplace=True)

            # Cleaning design file
            if clean_string:
                self.design.rename(index= lambda x:self._cleanStr(x),inplace=True)

            # Create a list of sampleIDs, but first check that they are present
            # in the wide data.
            self.sampleIDs = list()

            for sample in self.design.index.tolist():
                if sample in self.wide.columns:
                    self.sampleIDs.append(sample)
                else:
                    if self.logger:
                        self.logger.warn("Sample {0} missing on wide dataset".format(sample))
                    else:
                        print ("WARNING - Sample {0} missing on wide dataset".format(sample))


            for sample in self.wide.columns.tolist():
                if not (sample in self.design.index):
                    if keepSample:
                        if self.logger:
                            self.logger.warn("Sample {0} missing on design file".format(sample))
                        else:
                            print "WARNING - Sample {0} missing on design file".format(sample)
                    else:
                        if self.logger:
                            self.logger.error("Sample {0} missing on design file".format(sample))
                            raise
                        else:
                            print ("ERROR - Sample {0} missing on design file".format(sample))
                            raise

            # Drop design rows that are not in the wide data set
            self.design = self.design[self.design.index.isin(self.sampleIDs)]

            # Removing characters from data!!!!!!(EXPERIMENTAL)
            self.wide.replace(r'\D',np.nan,regex=True,inplace=True)

        except:
            print ("Error:", sys.exc_info()[0])
            raise

        # Save annotations
        self.anno = anno

        # Save runOrder
        self.runOrder = runOrder

        # Set up group information
        if group:
            if clean_string:
                self.group = self._cleanStr(group)
                self.design.columns = [self._cleanStr(x) for x in self.design.columns]
            else:
                self.group = group

            # combine group, anno and runorder
            if self.runOrder and self.anno:
                keep = [self.group, ] + [self.runOrder, ] + self.anno
            elif self.runOrder and not self.anno:
                keep = [self.group, ] + [self.runOrder, ]
            elif not self.runOrder and self.anno:
                keep = [self.group, ] + self.anno
            else:
                keep = [self.group, ]

            # Check if groups, runOrder and levels columns exist in the design file
            for elem in keep:
                if not(elem in self.design.columns):
                    if self.logger:
                        self.logger.error("Please make sure that '{0}' is written correctly or exists on your design file".format(elem))
                    else:
                        print ("Please make sure that '{0}' is written correctly or exists on your design file".format(elem))
                    raise ValueError

            # Check if columns exist on design file.
            self.design = self.design[keep]   # Only keep group columns in the design file
            self.design[self.group] = self.design[self.group].astype(str)   # Make sure groups are strings

            # Create list of group levels
            grp = self.design.groupby(self.group)
            self.levels = sorted(grp.groups.keys())  # Get a list of group levels
        else:
            self.group = None

        #Just keeping samples listed in design file
        if keepSample:
            self.keep_sample(self.sampleIDs)

    def _cleanStr(self, x):
        """ Clean strings so they behave.

        For some modules, uniqIDs and groups cannot contain spaces, '-', '*',
        '/', '+', or '()'. For example, statsmodel parses the strings and interprets
        them in the model.

        :Arguments:
            x (str): A string that needs cleaning

        :Returns:
            x (str): The cleaned string.

            self.origString (dict): A dictionary where the key is the new
                string and the value is the original string. This will be useful
                for reverting back to original values.

        """
        if isinstance(x, str):
            val = x
            x = re.sub(r'^-([0-9].*)', r'__\1', x)
            x = x.replace(' ', '_')
            x = x.replace('.', '_')
            x = x.replace('-', '_')
            x = x.replace('*', '_')
            x = x.replace('/', '_')
            x = x.replace('+', '_')
            x = x.replace('(', '_')
            x = x.replace(')', '_')
            x = x.replace('[', '_')
            x = x.replace(']', '_')
            x = x.replace('{', '_')
            x = x.replace('}', '_')
            x = x.replace('"', '_')
            x = x.replace('\'', '_')
            x = re.sub(r'^([0-9].*)', r'_\1', x)
            self.origString[x] = val
        return x

    def revertStr(self, x):
        """ Revert strings back to their original value so they behave well.

        Clean strings may need to be reverted back to original values for
        convience.

        :Arguments:
            x (str): A string that needs cleaning

            self.origString (dict): A dictionary where the key is the cleaned
                string and the value is the original string.

        :Returns:
            x (str): Original string.

        """
        if isinstance(x, str) and x in self.origString:
            x = self.origString[x]
        return x

    def melt(self):
        """ Convert a wide formated table to a long formated table.

        :Arguments:
            self.wide (pd.DataFrame): A wide formatted table with compound/gene
                as row and sample as columns.

            self.uniqID (str): The name of the unique identifier column in 'wide'
                (i.e. The column with compound/gene names).

            self.sampleIDs (list): An list of sampleIDs. These will correspond
                to columns in self.wide.

        :Returns:
            **Attributes**

            self.long (pd.DataFrame): Creates a new attribute called self.long
                that also has group information merged to the dataset.

        """
        melted = pd.melt(self.wide.reset_index(), id_vars=self.uniqID, value_vars=self.sampleIDs,
                         var_name='sampleID')
        melted.set_index('sampleID', inplace=True)
        self.long = melted.join(self.design).reset_index()   # merge on group information using sampleIDs as key

    def transpose(self):
        """ Transpose the wide table and merge on treatment information.

        :Arguments:
            self.wide (pd.DataFrame): A wide formatted table with compound/gene
                as row and sample as columns.

            self.design (pd.DataFrame): A table relating sampleID to groups.

        :Returns:
            merged (pd.DataFrame): A wide formatted table with sampleID as row
                and compound/gene as column. Also has column with group ID.

        """
        trans = self.wide[self.sampleIDs].T

        # Merge on group information using table index (aka 'sampleID')
        merged = trans.join(self.design)
        merged.index.name = 'sampleID'
        return merged

    def getRow(self, ID):
        """ Get a row corresponding to a uniqID.

        :Arguments:
            self.wide (pd.DataFrame): A wide formatted table with compound/gene
                as row and sample as columns.

            self.uniqID (str): The name of the unique identifier column in 'wide'
                (i.e. The column with compound/gene names).

            ID (str): A string referring to a uniqID in the dataset.

        :Returns:
            (pd.DataFrame): with only the corresponding rows from the uniqID.

        """
        return self.wide[self.wide[self.uniqID] == ID]

    def keep_sample(self, sampleIDs):
        """ 
        Keep only the given sampleIDs in the wide and design file.

        :Arguments:
            :param list sampleIDs: A list of sampleIDs to keep.

        :Returns:
            :rtype: wideToDesign
            :return: Updates the wideToDesign object to only have those sampleIDs.

        """
        self.sampleIDs = sampleIDs
        self.wide = self.wide[self.sampleIDs]
        self.design = self.design[self.design.index.isin(self.sampleIDs)]

    def removeSingle(self):
        """
        Removes groups with just one sample
        """
        if self.group:
            for level,current in self.design.groupby(self.group):
                if len(current) < 2:
                    self.design.drop(current.index, inplace=True)
                    self.wide.drop(current.index, axis=1, inplace=True)
                    if self.logger:
                        self.logger.warn("Your group '{0}' has only one element, "\
                            "this group is going to be removed from "\
                            "further calculations.".format(level))
                    else:                        
                        print ("Your group '{0}' has only one element, this "\
                        "group is going to be remove to perform further "\
                        "calculations.".format(level))

    def dropMissing(self):
        """
        Drops rows with missing data
        """
        # Asks if any missing value
        if np.isnan(self.wide.values).any():
            # Count original number of rows
            n_rows = len(self.wide.index)

            # Drop missing values
            self.wide.dropna(inplace=True)

            # Count the dropped rows
            n_rows_keeped = len(self.wide.index)

            # Logging!!!
            if self.logger:
                self.logger.warn("Missing values were found on wide data "\
                    "[{0}] rows were dropped.".
                    format(n_rows - n_rows_keeped))
            else:
                print ("Missing values were found on wide data "\
                    "[{0}] rows were dropped.".format(n_rows - n_rows_keeped))



class Flags:
    def __init__(self, index):
        """
        This class  creates an empty dataframe to hold the flag values for a dataset. The dataframe is created
        through instantiation and filled with 0's.

<<<<<<< HEAD:interface.py
        Arguments:
=======
class annoFormat:
    """ Class to handle generic data in a wide format with an associated design file. """
    def __init__(self, data, uniqID, mz, rt, anno=False, clean_string=True):
        """ Import and set-up data.
>>>>>>> secimtoolsV2:dataManager/interface.py

            :param index: List of values to be used as the index of the data frame
            :type index: list

            :param column: Column name for the dataframe
            :type column: string

        """
        # Create DataFrame from index and columns
        self.df_flags = pd.DataFrame(index=index)

        # Create a list to store column names
        self._columns = list()

    def _testIfIndexesMatch(self, mask):
        """
        Before laying a mask over the Flags DataFrame, test if the mask's
        indexes match to avoid errors.

        :Arguments:
            :param mask: List of True and False values corresponding to flag
                         values.
            :type mask: list

        :Returns:
            :type boolean: True or false if the indexes match

        """

        result = self.df_flags.index.isin(mask.index).any()
        return result

    def update(self, mask, column=''):
        """
        Update the dataframe with 1's if the mask value is true

        :Arguments:
            :param mask: List of mask values. Must follow same structure as instantiated flag dataframe
            :type mask: list

            :param column: Column name to update in the flag frame. Not required
            :type column: String

        :Returns:
            Updated instance of the flag dataframe. The dataframe can be accessed through '.df_flags'.

        """

        # Update the values to 1's if they are true in the mask
        if len(column) > 0:
            if self._testIfIndexesMatch(mask):
                self.df_flags.loc[mask.index, column] = mask.astype(int)
        else:
            self.df_flags.loc[mask.index, self._columns] = mask.astype(int)

    def addColumn(self, column, mask=[]):
        """
        Add a column to the flag DataFrame

        :Arguments:
            :param column: Name of the column to add to the DataFrame
            :type column: string | list of strings

            :param mask: List of True and False values corresponding to flag
                         values. OPTIONAL
            :type mask: list

        """
        self.df_flags[column] = 0

        # Store column names
        if isinstance(column, str):
            self._columns.append(column)
        else:
            self._columns.extend(column)

        # Update the column if a mask is given and the mask matches the index
        if len(mask) > 0:
            self.update(mask=mask, column=column)

    def fillNa(self):
        """
        Fill the flag DataFrame with np.nan
        """

        # Fill the 0's with numpy.nan
        self.df_flags.replace(0, np.nan, inplace=True)

<<<<<<< HEAD:interface.py
    def testOverlap(self, indices):
        """ Test if a list of indeces overlap. """

        # TODO: Trying to figure out the best algorithm to test if indeces are
        # the sam.
        for i, index in enumerate(indices):
            if i == 0:
                overlap = set(index)
            else:
                if overlap.intersection(set(index)):
                    overlap = overlap.union(set(index))

    def splitFlags(self):
        """ Split large DataFrame into individual DataFrames per column

        :Returns:
            :rtype: dictionary
            :returns: Dictionary of pandas.DataFrame

        """
        # List to hold dataframes
        df_list= []
=======
            #Trying to import
            self.data = pd.read_table(data)

            if clean_string:
                self.data[self.uniqID] = self.data[self.uniqID].apply(lambda x: self._cleanStr(x))
                self.data.rename(columns= lambda x:self._cleanStr(x),inplace=True)

            # Make sure index is a string and not numeric
            self.data[self.uniqID] = self.data[self.uniqID].astype(str)

            # Set index to uniqID column
            self.data.set_index(self.uniqID, inplace=True)

            # If not annotation then ignoring additional columns
            self.anno = None
            if not(anno):
                self.data = self.data[[self.mz,self.rt]]
            else:
                self.anno = self.data.columns.tolist()
                self.anno.remove(self.mz)
                self.anno.remove(self.rt)                
        except:
            print ("Please make sure that your data file have columns called '{0}','{1}' and '{2}'.".format(uniqID,mz,rt))
            raise ValueError
>>>>>>> secimtoolsV2:dataManager/interface.py

        # Loop through columns and build a dataframe
        for column in self._columns:
            exec('df_' + str(column) + '= pd.DataFrame(' +
                    'data=self.df_flags[column], index=self.df_flags.index,' +
                    'columns=[column])')
            # Add newly created DataFrame to df dictionary
            exec('df_dict.append(df_' + str(column) + ')')

        # Return df_dict
        return df_list

    @staticmethod
    def _mergeIndex(indices):
        """ Function to check for overlap for a list of indices.

        This function is based on:
        http://stackoverflow.com/questions/9110837/python-simple-list-merging-based-on-intersections

        :param list indices: A list of pd.Index

        """
        # Convert index into set
        sets = [set(ind) for ind in indices if len(ind)]
        merged = 1
        while merged:
            merged = 0
            results = []
            while sets:
                common, rest = sets[0], sets[1:]
                sets = []
                for x in rest:
                    if x.isdisjoint(common):
                        # If they don't overlap then append
                        sets.append(x)
                    else:
                        # If they overlap, take the union
                        merged = 1
                        common |= x
                results.append(common)
            sets = results
        return sets

    @staticmethod
    def merge(flags):
        """
        Merge a list of DataFrames. This method will check to make sure all of the indices are the same for each
        DataFrame and will then return one merged DataFrame.

        :Arguments:

            :param flags: List of DataFrames
            :type flags: list

        :Returns:

            :return: DataFrame of merged flags
            :rtype: pandas.DataFrame

        """
        # Check the index of each dataframe before trying to merge
        mergeIndex = Flags._mergeIndex([x.index for x in flags])

        if len(mergeIndex) == 1:
            # Merge all flags together
            # NOTE: Pandas cannot store NAN values as a int. If there are NAN
            # then the column is converted to a float.
            df_mergedFlags = pd.concat(flags, axis=1)

            # Return merged flag file
            return df_mergedFlags
        else:
            print "Not all indexes overlap. Check that flags are features OR \
                   samples."
            raise SystemExit

if __name__ == '__main__':
    pass
