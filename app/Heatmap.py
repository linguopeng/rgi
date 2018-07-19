
from app.settings import *
from seaborn import heatmap
import math, os, json, csv
import numpy as np
import pandas as pd
from collections import defaultdict, Counter
from argparse import ArgumentParser
from textwrap import wrap
import matplotlib # this needs to be added to run on galaxylab
matplotlib.use('Agg') # this needs to be added to run on galaxylab
from matplotlib import gridspec
import seaborn as sns
import matplotlib.pyplot as plt

class Heatmap(object):
    """
    This is a program that genreates a heatmap of multiple RGI analyses.
    """

    def __init__(self, input, classification, frequency, output, cluster, debug):
        self.input = input
        self.classification = classification
        self.frequency = frequency
        self.output = output
        self.cluster = cluster
        self.debug = debug

        if self.debug:
            logger.setLevel(10)

    def __repr__(self):
        """Returns Heatmap class full object."""
        return "Heatmap({}".format(self.__dict__)

    def get_figure_dimensions(self,s,g):
        """Set the dimensions of the figure"""
        w = len(s)
        l = len(g)
        figsize = (w, l)
        fig = plt.figure(figsize = figsize)
        # print(figsize)
        return w,l,fig,figsize

    def create_plot(self,t,r): # t = type plot, r = ratio
        # ax0 = heatmap, ax1 = categories, ax2 = frequency
        """Creates the appropriate number of subplots"""
        if t == 'c': # Category
            gs = gridspec.GridSpec(1, 2, width_ratios=[1,r])
            ax0 = plt.subplot(gs[1]) # Heatmap
            ax1 = plt.subplot(gs[0], sharey=ax0) # Categories
            ax1.set_xlim([0,1])
            ax1.spines['right'].set_visible(False)
            ax1.spines['top'].set_visible(False)
            ax1.spines['bottom'].set_visible(False)
            ax1.spines['left'].set_visible(False)
            ax1.tick_params(bottom=False, left=False)
            return ax0,ax1,gs
        if t == 'cf': # Category and frequency
            gs = gridspec.GridSpec(2, 2, width_ratios=[1,r], height_ratios=[1,50])
            ax0 = plt.subplot(gs[3])
            ax1 = plt.subplot(gs[2], sharey=ax0)
            ax1.set_xlim([0,1])
            ax1.spines['right'].set_visible(False)
            ax1.spines['top'].set_visible(False)
            ax1.spines['bottom'].set_visible(False)
            ax1.spines['left'].set_visible(False)
            ax1.tick_params(bottom=False, left=False)
            ax2 = plt.subplot(gs[1], sharex=ax0)
            ax2.spines['right'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            ax2.tick_params(bottom=False)
            plt.setp(ax2.get_xticklabels(), visible=False)
            ax2.set_axisbelow(True)
            plt.grid(axis='y')
            return ax0,ax1,ax2,gs
        if t == 'f': # Frequency
            gs = gridspec.GridSpec(2, 1, height_ratios=[1,50])
            ax0 = plt.subplot(gs[1])
            ax2 = plt.subplot(gs[0], sharex=ax0)
            ax2.set_xlim([0,1])
            ax2.spines['right'].set_visible(False)
            ax2.spines['top'].set_visible(False)
            ax2.tick_params(bottom=False)
            plt.setp(ax2.get_xticklabels(), visible=False)
            return ax0,ax2,gs

    def create_class_series(self, class_dict, name):
        """Create a pandas series for the classification chosen"""
        class_df = pd.Series(class_dict, name=name)
        class_df.index.name = "model_name"
        class_df = class_df.apply(tuple)
        class_df.reset_index()
        return class_df

    def create_categories(self, class_dict, df):
        """Reformats the dataframe to handle categorization data"""
        for model in class_dict:
            if len(class_dict[model]) > 1:
                df = df.append([df.loc[model]]*(len(class_dict[model])-1))

        # Assigns a unique identifier to each entry to index the dataframe without duplicates
        count = Counter(df.index.values)
        new_labels = df.index.tolist() # Add * to the models with duplicates
        new_index = []
        counted = {}
        for model in list(df.index.values):
            if count[model] > 1:
                idx = new_labels.index(model)
                new_labels[idx] = "%s*" % (model)

        for i,v in enumerate(list(df.index.values)):
            if v in counted:
                counted[v] += 1
                new_index.append(v+"_"+str(counted[v]))
            else:
                counted[v] = 0
                new_index.append(v+"_0")

        df.index = new_labels
        df = df.assign(uID=new_index)
        df = df.reset_index().set_index("uID")
        return df

    def create_frequency_df(self, df, outfile):
        """Creates a dataframe for frequency data"""
        freq_df = pd.DataFrame() # New matrix df based on frequencies
        freq_dict = {} # Dictionary to keep track of ocurance of resistome profile
        samples = {} # Dictionary to group samples with identifcal profiles together
        n = 0
        for column in df:
            if column != 'index':
                n += 1
            s1 = df.loc[:, column] # Store column data as a Series
            if freq_df.empty:
                freq_df = pd.concat([freq_df, s1], axis = 1, sort=True)
                freq_dict[column] = 1
                samples[column] = [column]
            else:
                counter = 0
                for profile in freq_df:
                    # print(profile)
                    s2 = df.loc[:, profile]
                    if s1.equals(s2):
                        counter += 1
                        freq_dict[profile] += 1
                        samples[profile].append(column)
                        break
                if counter == 0:
                    freq_df = pd.concat([freq_df, s1], axis=1, sort=True)
                    freq_dict[column] = 1
                    samples[column] = [column]
        try:
            del freq_dict["index"]
            del samples["index"]
        except:
            pass

        # Order columns by frequency of resistome profiles
        cols = sorted(samples.keys(), key=(lambda x: len(samples[x])), reverse=True)
        if self.classification:
            cols.insert(0, 'index')
        freq_df = freq_df[cols]

        with open(outfile + str(n) + '-frequency.txt', 'w') as f:
            fcsv = csv.writer(f, delimiter='\t')
            fcsv.writerow(['Frequency', 'Samples'])
            for s in cols:
                if s != 'index':
                    fcsv.writerow([len(samples[s])] + [', '.join(map(str, samples[s]))])
            # for k,v in samples.items():
            #     fcsv.writerow([len(v)] + [', '.join(map(str, v))])
        # create_frequency_df.freq_dict = freq_dict
        return freq_df, freq_dict

    def draw_barplot(self, freq_dict, ax2):
        """Draws the frequency barplot"""
        from matplotlib.ticker import MaxNLocator
        y = list(freq_dict.values())
        yint = range(min(y), math.ceil(max(y)))
        bp = ax2.bar(range(len(freq_dict)), sorted(freq_dict.values(), reverse=True), color="k", align="edge")
        ax2.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax2.set_ylabel("Profile Frequency", rotation=0, va='center', labelpad=150, fontsize='xx-large')

    def cluster_data(self, option, df):
        """Hierarchically clusters the dataframe"""
        if option == "samples":
            cm = sns.clustermap(df, row_cluster=False, col_cluster=True)
            global clustered_col
            clustered_col = cm.dendrogram_col.reordered_ind
            df = df.iloc[:, clustered_col]
        elif option == "genes":
            cm = sns.clustermap(df, row_cluster=True, col_cluster=False)
            clustered_row = cm.dendrogram_row.reordered_ind
            df = df.iloc[clustered_row, :]
        elif option =="both":
            cm = sns.clustermap(df, row_cluster=True, col_cluster=True)
            clustered_col = cm.dendrogram_col.reordered_ind
            clustered_row = cm.dendrogram_row.reordered_ind
            df = df.iloc[clustered_row, clustered_col]
        return df

    def calculate_categories(self, series):
        """Creates category labels"""
        freq = series.value_counts()
        freq = freq.sort_index()
        categories = freq.index.values
        # Introduces a line break if the category name is too long
        categories = ['\n'.join(wrap(cat,40)) for cat in categories]
        ranges = freq.values
        return categories, ranges

    def draw_categories(self, ax1, ranges, cat_list):
        """Draws on the categorization axis"""
        # Draw first category first
        ax1.plot([1,1], [0,ranges[0]], lw=10) # coloured lines
        ax1.text(0.5, (ranges[0]/2), cat_list[0], horizontalalignment="center", fontsize='xx-large')
        i = 0
        # Automate drawing of the rest of the categories
        for x in ranges[1:]: #skips first item
            i += 1
            ymax = (math.fsum(ranges[0:i]) + x)
            ymin = math.fsum(ranges[0:i])
            ax1.plot([1,1], [ymin, ymax], lw = 10)
            ax1.text(0.5, (ymin + (ymax - ymin)/2), cat_list[i], fontsize='xx-large', horizontalalignment="center")

    def get_axis_size(self, fig, ax):
        """Retunrs the width and length of a subplot axes"""
        bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        width, height = bbox.width, bbox.height
        return width, height


    def run(self):
        # print args
        logger.info(json.dumps(self.__dict__, indent=2))

        # List to hold the file name
        directory = self.input
        files = os.listdir(directory)
        jsons = []
        shortened = []
        for thing in files:
            file_path = os.path.join(directory, thing)
            if thing.endswith(".json") and os.path.isfile(file_path): # Check if it's a file
                jsons.append(thing)
        genelist = [] # List of unique genes
        genes = {} # Will become the dataframe
        resist_mech = {} # key: gene, value: resistance mechanism
        drug_class = {} # key: gene, value: drug class
        gene_family = {} # key: gene, value: gene family
        excluded = [] # incompletely curated models
        for jsonfile in jsons:
            # {json file: {Model: type_hit}}
            accession = jsonfile.split(".")[0]
            shortened.append(accession) # Don't take whole file name
            genes[accession] = {}
            with open(os.path.join(directory, jsonfile)) as data: # Use os.path.join
                rgi_data = json.load(data)
            try:
                del rgi_data["_metadata"]
            except:
                pass

            try:
                tophits = {}
                # Top hit of each ORF
                for key,value in rgi_data.items():
                    if isinstance(value, dict):
                        contig_id = key
                        hsp = max(value.keys(), key=(lambda key: value[key]['bit_score']))

                        # Flag to exclude loose hits
                        if value[hsp]["type_match"] != "Loose":
                            topmodel = value[hsp]["model_name"]
                            tophits[topmodel] = value[hsp]["type_match"]

                            # Build dictionary of model names and their classifications
                            try:
                                if self.classification:
                                    rm = 0
                                    gf = 0
                                    dc = 0
                                    for entry in value[hsp]["ARO_category"]:
                                        if value[hsp]["ARO_category"][entry]["category_aro_class_name"] == "Resistance Mechanism":
                                            rm += 1
                                            if value[hsp]["model_name"] not in resist_mech:
                                                resist_mech[value[hsp]["model_name"]] = [value[hsp]["ARO_category"][entry]["category_aro_name"]]
                                            else:
                                                if value[hsp]["ARO_category"][entry]["category_aro_name"] not in resist_mech[value[hsp]["model_name"]]:
                                                    resist_mech[value[hsp]["model_name"]].append(value[hsp]["ARO_category"][entry]["category_aro_name"])

                                # Drug classes classification
                                        elif value[hsp]["ARO_category"][entry]["category_aro_class_name"] == "Drug Class":
                                            dc += 1
                                            if value[hsp]["model_name"] not in drug_class:
                                                drug_class[value[hsp]["model_name"]] = [value[hsp]["ARO_category"][entry]["category_aro_name"]]
                                            else:
                                                if value[hsp]["ARO_category"][entry]["category_aro_name"] not in drug_class[value[hsp]["model_name"]]:
                                                    drug_class[value[hsp]["model_name"]].append(value[hsp]["ARO_category"][entry]["category_aro_name"])

                                # Gene Family classification
                                        elif value[hsp]["ARO_category"][entry]["category_aro_class_name"] == "AMR Gene Family":
                                            gf += 1
                                            if value[hsp]["model_name"] not in gene_family:
                                                gene_family[value[hsp]["model_name"]] = [value[hsp]["ARO_category"][entry]["category_aro_name"]]
                                            else:
                                                if value[hsp]["ARO_category"][entry]["category_aro_name"] not in gene_family[value[hsp]["model_name"]]:
                                                    gene_family[value[hsp]["model_name"]].append(value[hsp]["ARO_category"][entry]["category_aro_name"])

                                    # Flag to exclude model if it doesn't have classification for rm, gf, or dc
                                    if any(x == 0 for x in [rm, gf, dc]):
                                        del tophits[topmodel]
                                        if topmodel not in excluded:
                                            excluded.append(topmodel)
                                        try:
                                            del resist_mech[topmodel]
                                        except:
                                            pass
                                        try:
                                            del gene_family[topmodel]
                                        except:
                                            pass
                                        try:
                                            del drug_class[topmodel]
                                        except:
                                            pass
                                        # print(jsonfile, hsp)
                                        # print("NOTE: %s excluded because it is missing complete categorization information." % (topmodel))

                            except Exception as e:
                                print(e)
                        else:
                            print("Loose hit encountered. Not being added.")
                # Populates the matrix of typehits
                genes[accession] = tophits
                for x in tophits:
                    if x not in genelist:
                        genelist.append(x)
            # except Exception as e:
            #     print(e)
            except:
                pass

        for e in excluded:
            print("NOTE: %s excluded because it is missing complete categorization information." % (e))

        genelist = sorted(genelist)

        # Create a dictionary that will convert type of hit to num. value
        conversion = {"Perfect": 2, "Strict": 1}

        # Apply conversion so hit criteria is number based
        for sample in genes:
            for gene in genes[sample]:
                genes[sample][gene] = conversion[genes[sample][gene]]
            for thing in genelist:
                if thing not in genes[sample]:
                    genes[sample][thing] = 0

        # Create dataframe from genes dictionary
        df = pd.DataFrame.from_dict(genes) # If df is empty - then what?
        # sns.set(font_scale=1.7)

        # If the classification option chosen:
        if self.classification:
            global ax0
            if self.classification == "drug_class":
                df = self.create_categories(drug_class, df)
            elif self.classification == "resistance_mechanism":
                df = self.create_categories(resist_mech, df)
            elif self.classification == "gene_family":
                df = self.create_categories(gene_family, df)

            # Create 3 series, one for each classification type
            class_df1 = self.create_class_series(drug_class, "drug_class")
            class_df2 = self.create_class_series(resist_mech, "resistance_mechanism")
            class_df3 = self.create_class_series(gene_family, "gene_family")

            # Combine the 3 Series into a dataframe with all classification info
            complete_class_df = pd.concat([class_df1, class_df2, class_df3], axis=1, sort=True)

            # Function if possible
            if self.classification == "drug_class":
                classification = "Drug Class"
                complete_class_df= complete_class_df.set_index(["resistance_mechanism", "gene_family"], append=True)["drug_class"].apply(pd.Series).stack()
                complete_class_df= complete_class_df.reset_index()
                complete_class_df.columns = ["model_name", "resistance_mechanism", "gene_family", "number", "drug_class"]
                complete_class_df= complete_class_df.set_index("model_name")
                complete_class_df= complete_class_df.drop(["number"], axis=1)
            elif self.classification == "resistance_mechanism":
                classification = "Resistance Mechanism"
                complete_class_df= complete_class_df.set_index(["drug_class", "gene_family"], append=True)["resistance_mechanism"].apply(pd.Series).stack()
                complete_class_df= complete_class_df.reset_index()
                complete_class_df.columns = ["model_name", "drug_class", "gene_family", "number", "resistance_mechanism"]
                complete_class_df= complete_class_df.set_index("model_name")
                complete_class_df= complete_class_df.drop(["number"], axis=1)
            elif self.classification == "gene_family":
                classification = "AMR Gene Family"
                complete_class_df= complete_class_df.set_index(["drug_class", "resistance_mechanism"], append=True)["gene_family"].apply(pd.Series).stack()
                complete_class_df= complete_class_df.reset_index()
                complete_class_df.columns = ["model_name", "drug_class", "resistane_mechanism", "number", "gene_family"]
                complete_class_df= complete_class_df.set_index("model_name")
                complete_class_df= complete_class_df.drop(["number"], axis=1)

            # Create unique identifiers again for the classifications dataframe
            new_index = []
            counted = {}
            for i,v in enumerate(list(complete_class_df.index.values)):
                if v in counted:
                    counted[v] += 1
                    new_index.append(v+"_"+str(counted[v]))
                else:
                    counted[v] = 0
                    new_index.append(v+"_0")

            complete_class_df = complete_class_df.assign(uID=new_index)
            complete_class_df = complete_class_df.reset_index().set_index("uID")
            s = complete_class_df.loc[:,self.classification]
            # calculate_categories(s)

            complete_class_df = complete_class_df.sort_values(by=[self.classification, 'model_name'])
            unique_ids = list(complete_class_df.index.values)
            df = df.reindex(index=unique_ids)

            # Modifies dataframe if cluster option chosen
            if self.cluster == "samples":
                df_copy = df.drop(["index"], axis=1)
                df_copy = self.cluster_data(self.cluster, df_copy)
                df = df.set_index("index", append=True)
                df = df.iloc[:, clustered_col]
                df = df.reset_index().set_index("uID")
            elif self.cluster == "both" or self.cluster == "genes":
                print("Error: Unable to cluster genes because the categorization option was chosen. No heatmap will be generated. Closing program now.")
                exit()

            # Figure parameters if frequency option chosen
            if self.frequency == "on":
                df, freq_dict = self.create_frequency_df(df, self.output)
                df = df.reindex(index=unique_ids)
                df = df.set_index("index")

                # Set the figure size
                fig_width,fig_length,fig,figsize = self.get_figure_dimensions(jsons, unique_ids)

                # Try to draw plot with default sizing
                ax0,ax1,ax2,gs = self.create_plot('cf', 4)

                # Adjust the dimensions
                while True:
                    desired_width = (self.get_axis_size(fig,ax0)[1])/2
                    if self.get_axis_size(fig,ax0)[0] > (self.get_axis_size(fig,ax0)[1])/2:
                        # print('hehe')
                        break
                    if self.get_axis_size(fig,ax0)[1] > 100:
                        fig_length = fig_length/2
                        figsize = (fig_width, fig_length)
                        desired_width = (self.get_axis_size(fig,ax0)[1])/2
                        figsize = (desired_width, fig_length)
                        fig = plt.figure(figsize = figsize)
                        ax0,ax1,ax2,gs = self.create_plot('cf', 4)
                    if self.get_axis_size(fig,ax0)[0] < desired_width:
                        fig_length = fig_length/2
                        figsize = (fig_width, fig_length)
                        desired_width = (self.get_axis_size(fig,ax0)[1])/2
                        figsize = (desired_width, fig_length)
                        fig = plt.figure(figsize = figsize)
                        ax0,ax1,ax2,gs = self.create_plot('cf', 4)

                # Calculate correct categories dimensions to use
                ratio_to_use = math.floor(float(get_axis_size(fig,ax0)[0])/8)
                # print(ratio_to_use)
                # print(get_axis_size(fig,ax1))
                if figsize[1] > 100:
                    sns.set(font_scale=1.7)
                elif 80 < figsize[1] < 100:
                    sns.set(font_scale=1.2)
                sns.set_style("white")
                ax0,ax1,ax2,gs = self.create_plot('cf', ratio_to_use)
                # print(get_axis_size(fig,ax1))
                # print(figsize)

                # Create the heatmap
                print(figsize)
                g = sns.heatmap(df, cmap="viridis", cbar=False, ax=ax0)
                plt.setp(g.yaxis.get_ticklabels(), rotation=0, fontsize='xx-large')
                plt.setp(g.xaxis.get_ticklabels(), visible=False)
                g.tick_params(bottom=False)
                g.set_xlabel(" ")
                g.yaxis.set_label_position("left")
                g.set_ylabel(" ")
                plt.setp(ax1.get_yticklabels(), visible=False)
                plt.setp(ax1.get_xticklabels(), visible=False)

                # Draw categories
                self.draw_categories(ax1, self.calculate_categories(s)[1], self.calculate_categories(s)[0])

                # Draw barplot
                self.draw_barplot(freq_dict,ax2)

                # Save figure
                gs.tight_layout(fig)
                file_name = '%s-%s' %(self.output, str(len(jsons)))
                # print(file_name)
                # plt.savefig(self.output + '-' + str(len(jsons)) +".eps", bbox_inches="tight", format="eps")
                plt.savefig(file_name + '.eps', bbox_inches="tight", format="eps")
                plt.savefig(file_name + '.png', bbox_inches="tight", format="png")
                if self.cluster == "samples":
                    print('Output file %s: AMR genes categorised by %s and only unique '
                    'resistome profiles are displayed with ther frequency and have been '
                    'clustered hierarchically (see SciPy documentation). Yellow '
                    'represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit. Genes with asterisks (*) appear multiple times '
                    'because they belong to more than one %s category in the '
                    'antibiotic resistance ontology (ARO).' %(file_name, classification, classification))
                else:
                    print('Output file %s: AMR genes categorised by %s and only unique '
                    'resistome profiles are displayed with ther frequency Yellow '
                    'represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit. Genes with asterisks (*) appear multiple times '
                    'because they belong to more than one %s category in the '
                    'antibiotic resistance ontology (ARO).' %(file_name, classification, classification))

            # Categories, but no frequency
            else:
                df = df.set_index("index")
                # df.to_csv('hehe.csv')

                # Set the dimension parameters
                fig_width,fig_length,fig,figsize = self.get_figure_dimensions(jsons, unique_ids)

                # Try to draw plot with default sizing
                ax0,ax1,gs = self.create_plot('c', 4)
                print(self.get_axis_size(fig,ax0))

                # Adjust the dimensions
                while True:
                    desired_width = (self.get_axis_size(fig,ax0)[1])/2

                    if self.get_axis_size(fig,ax0)[0] > (self.get_axis_size(fig,ax0)[1])/2:
                        # print('hehe')
                        break
                    if self.get_axis_size(fig,ax0)[1] > 100:
                        fig_length = fig_length/2
                        figsize = (fig_width, fig_length)
                        desired_width = (self.get_axis_size(fig,ax0)[1])/2
                        figsize = (desired_width, fig_length)
                        fig = plt.figure(figsize = figsize)
                        ax0,ax1,gs = self.create_plot('c', 4)
                        print('eeeee')
                    if self.get_axis_size(fig,ax0)[0] < desired_width:
                        fig_length = fig_length/2
                        figsize = (fig_width, fig_length)
                        desired_width = (self.get_axis_size(fig,ax0)[1])/2
                        figsize = (desired_width, fig_length)
                        fig = plt.figure(figsize = figsize)
                        ax0,ax1,gs = self.create_plot('c', 4)
                        break

                # Calculate correct categories dimensions to use
                ratio_to_use = math.floor(float(self.get_axis_size(fig,ax0)[0])/8)
                # print(ratio_to_use)
                # print(get_axis_size(fig,ax1))
                if figsize[1] > 100:
                    sns.set(font_scale=1.7)
                elif 80 < figsize[1] < 100:
                    sns.set(font_scale=1.2)
                sns.set_style("white")
                ax0,ax1,gs = self.create_plot('c', ratio_to_use)
                # print(get_axis_size(fig,ax0))
                # print(get_axis_size(fig,ax1))
                # print(figsize)

                # Create the heatmap
                print(figsize)
                g = sns.heatmap(df, cmap="viridis", cbar=False, ax=ax0)
                plt.setp(g.yaxis.get_ticklabels(), rotation=0, fontsize='xx-large')
                plt.setp(g.xaxis.get_ticklabels(), rotation=90, fontsize='xx-large')
                plt.setp(ax1.get_yticklabels(), visible=False)
                plt.setp(ax1.get_xticklabels(), visible=False)
                g.set_ylabel(" ")
                g.set_xlabel(" ")
                # plt.setp(ax0, title="Hits Predicted by RGI to Models in CARD")
                self.draw_categories(ax1, self.calculate_categories(s)[1], self.calculate_categories(s)[0])
                # print(figsize)

                # Save figure
                gs.tight_layout(fig)
                file_name = '%s-%s' %(self.output, str(len(jsons)))
                # print(file_name)
                # plt.savefig(self.output + '-' + str(len(jsons)) +".eps", bbox_inches="tight", format="eps")
                plt.savefig(file_name + '.eps', bbox_inches="tight", format="eps")
                plt.savefig(file_name + '.png', bbox_inches="tight", format="png")
                if self.cluster == "samples":
                    print('Output file %s: AMR genes categorised by %s and samples have been '
                    'clustered hierarchically (see SciPy documentation). Yellow '
                    'represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit. Genes with asterisks (*) appear multiple times '
                    'because they belong to more than one %s category in the '
                    'antibiotic resistance ontology (ARO).' %(file_name, classification, classification))
                else:
                    print('Output file %s: AMR genes categorised by %s. Yellow '
                    'represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit. Genes with asterisks (*) appear multiple times '
                    'because they belong to more than one %s category in the '
                    'antibiotic resistance ontology (ARO).' %(file_name, classification, classification))

        # No categories
        else:
            if self.frequency == "on":
                from matplotlib.ticker import MaxNLocator
                if self.cluster:
                    df = self.cluster_data(self.cluster, df)

                # Set the dimension parameters
                fig_width,fig_length,fig,figsize = self.get_figure_dimensions(jsons, genelist)

                # Try to draw plot with default sizing
                if figsize[1] > 100:
                    sns.set(font_scale=1.7)
                elif 80 < figsize[1] < 100:
                    sns.set(font_scale=1.2)
                sns.set_style("white")
                ax0,ax2,gs = self.create_plot('f', 0)
                df,freq_dict = self.create_frequency_df(df, self.output)

                # Create the heatmap
                print(figsize)
                g = sns.heatmap(df, cmap="viridis", cbar=False, ax=ax0)
                plt.setp(g.yaxis.get_ticklabels(), rotation=0, fontsize='xx-large')
                plt.setp(g.xaxis.get_ticklabels(), visible=False)
                g.tick_params(bottom="off")
                g.yaxis.set_label_position("left")
                g.set_ylabel(" ")
                g.set_xlabel(" ")

                # Draw barplot
                self.draw_barplot(freq_dict,ax2)

                # Save figure
                gs.tight_layout(fig)
                file_name = '%s-%s' %(self.output, str(len(jsons)))
                # print(file_name)
                # plt.savefig(self.output + '-' + str(len(jsons)) +".eps", bbox_inches="tight", format="eps")
                plt.savefig(file_name + '.eps', bbox_inches="tight", format="eps")
                plt.savefig(file_name + '.png', bbox_inches="tight", format="png")
                if self.cluster == 'samples':
                    print('Output file %s: AMR genes are listed in alphabetical order and unique '
                    'resistome profiles are displayed with their frequency have been '
                    'clustered hierarchically (see SciPy documentation). Yellow '
                    'represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit.' %(file_name))
                elif self.cluster == 'genes':
                    print('Output file %s: AMR genes have been clustered hierarchically '
                    '(see SciPy documentation) and unique resistome profiles are '
                    'displayed with ther frequency. Yellow represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit.' %(file_name))
                elif self.cluster == 'both':
                    print('Output file %s: AMR genes and unique resistome profiles '
                    'displayed with ther frequency have been clustered hierarchically '
                    '(see SciPy documentation). Yellow represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit.' %(file_name))
                else:
                    print('Output file %s: AMR genes are listed in alphabetical order and unique '
                    'resistome profiles are displayed with their frequency. Yellow '
                    'represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit.' %(file_name))

            else:
                # No categories or frequency
                if self.cluster:
                    df = self.cluster_data(self.cluster, df)

                # Set the dimension parameters
                fig_width,fig_length,fig,figsize = self.get_figure_dimensions(jsons, genelist)

                if figsize[1] > 100:
                    sns.set(font_scale=1.7)
                elif 80 < figsize[1] < 100:
                    sns.set(font_scale=1.2)
                sns.set_style("white")

                # Create the heatmap
                print(figsize)
                g = sns.heatmap(df, cmap='viridis', cbar=False)
                plt.setp(g.yaxis.get_ticklabels(), rotation=0, fontsize='xx-large')
                plt.setp(g.xaxis.get_ticklabels(), rotation=90, fontsize='xx-large')
                g.set_ylabel(" ")
                g.set_xlabel(" ")

                # Save figure
                file_name = '%s-%s' %(self.output, str(len(jsons)))
                # print(file_name)
                # plt.savefig(self.output + '-' + str(len(jsons)) +".eps", bbox_inches="tight", format="eps")
                plt.savefig(file_name + '.eps', bbox_inches="tight", format="eps")
                plt.savefig(file_name + '.png', bbox_inches="tight", format="png")
                if self.cluster == 'samples':
                    print('Output file %s: AMR genes are listed in alphabetical order '
                    'and samples have been clustered hierarchically (see SciPy documentation). '
                    'Yellow represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit.' %(file_name))
                elif self.cluster == 'genes':
                    print('Output file %s: AMR genes have been clustered hierarchically. '
                    'Yellow represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit.' %(file_name))
                elif self.cluster == 'both':
                    print('Output file %s: AMR genes and samples have been clustered hierarchically '
                    '(see SciPy documentation). Yellow represents a perfect hit, teal represents a strict hit, purple '
                    'represents no hit.' %(file_name))
                else:
                    print('Output file %s: Yellow represents a perfect hit, '
                    'teal represents a strict hit, purple represents no hit.' %(file_name))