
# coding: utf-8

import os.path
import pandas as pd
import numpy as np
import time
import datetime

def begin():
    file_path, id_col, group_col, match_col, save_to_filename = static_vars()
    data = read_file(file_path, id_col)
    save_csv_filename = screen_filename(save_to_filename)
    data_minus_exact_matches, matches_df, exact_match_count = exact_match(data, group_col, match_col)
    matches_df = fuzzy_match(data_minus_exact_matches, 
                             matches_df, 
                             group_col,
                             match_col,
                             count = exact_match_count
                             )
    
    df_to_csv(matches_df, save_csv_filename)



def screen_filename(save_to_filename):
    if os.path.isfile(save_to_filename):
        save_to_filename = screen_filename_request(save_to_filename)
        save_to_filename = screen_filename(save_to_filename)
        return save_to_filename
    else:        
        print ('Destination filename and path allowable.')
        return save_to_filename



def manual_filename():        
    save_to_filename = input("Please enter a new filename and path ie. C:\\Users\\your_username\\Documents\\data.csv (include .csv as the extension)\n")
    if '.csv' in save_to_filename[-4:]:
        return save_to_filename
    else:
        print('Not detecting proper extension. Please add .csv to file name.')
        save_to_filename = manual_filename()
        return save_to_filename



def screen_filename_request(save_to_filename):
    print ('Destination filename already exists')
    r = input('Timestamp this filename? y/n\n Typing n will allow you to enter a filename/path manually\n')
    if r == 'y':
        now = datetime.datetime.now()         
        tmstmp = str(now.month) + '-' + str(now.day) + '-' + str(now.year) + '_' + str(now.hour) + str(now.minute)
        save_to_filename = save_to_filename.split('.csv')
        save_to_filename[-1] = save_to_filename[-1] + '_' + tmstmp + '.csv'
        save_to_filename = ''.join(save_to_filename)        
        return save_to_filename
    
    elif r == 'n':
        save_to_filename = manual_filename()
        return save_to_filename
    
    else:
        print ("Please enter either y or n.")
        save_to_filename = screen_filename(save_to_filename)    
        return save_to_filename
        



def read_file(file_path, id_col):
    data = pd.read_csv(file_path, index_col = id_col) 
    data['ID'] = data.index
    print ('Source file loaded.')
    return data



def exact_match(data, group_col, match_col):
    
    #group_col is the category column
    #match_col is the value used to match the categories
    
    #Create dataframe that will store matches
    matches_df = pd.DataFrame()
    
    #Divide into two groups/tables
    control_pool, exp = data.groupby(group_col)
    
    #Left join on probability/score. This is the 'matching' part. 
    #There is probably a better way to do this but joining tables on a  certain value is reliable.
    df = pd.merge(exp[1], control_pool[1], how = 'left', on = match_col)
    
    #Drop duplicates
    df = df.drop_duplicates(subset = 'ID_y')
    df = df.drop_duplicates(subset = 'ID_x')

    #Drop na/empty values. Why were they generated from the left join in the first place?
    df = df.dropna(subset = ['ID_y'])
    df = df.dropna(subset = ['ID_x']) 

    #Add the matches to existing df matches_df
    matches_df['Control'] = df['ID_y'].astype(int)
    matches_df['Experiment'] = df['ID_x'].astype(int)
    
    data_minus_exact_matches = data.drop(matches_df['Control'])
    data_minus_exact_matches = data_minus_exact_matches.drop(matches_df['Experiment'])
    
    exact_match_count = matches_df.shape[0]
    
    print ("{} exact matches found. Beginning default (caliper of .0001) fuzzy matching beep boop beep...".format(exact_match_count))
            
    return data_minus_exact_matches, matches_df, exact_match_count



def fuzzy_match(data_minus_exact_matches, matches_df, group_col,match_col, count, start = time.time(),  previous_caliper = .0001, caliper = .0005, walk = True):

    #Create list to walk-through of incremental caliper values ie. [ 0.005,  0.006,  0.007,  0.008,  0.009]
    caliper_increment = float(abs(float(previous_caliper) - float(caliper))/5)
    caliper_list = np.arange(float(previous_caliper), float(caliper), caliper_increment)
    start = time.time()

    #Iterate through caliper list
    for cal in caliper_list:

        #Simply for measuring duration of matching

        #Split data into two groups
        if len(data_minus_exact_matches[group_col].unique()) > 1:
            control, exp = data_minus_exact_matches.groupby(group_col)

            fuzzy_matches = fuzzy_match_worker(control, exp, cal, match_col)

            matches_len = len(fuzzy_matches)

            if matches_len > 0:
                #Create dataframe from dictionary
                final_df = build_clean_new_matches(fuzzy_matches)
                #Concat matches to existing dataframe
                matches_df_concat = [matches_df, final_df]
                matches_df = pd.concat(matches_df_concat)

                #Rebuild source data for next fuzzy matching
                data_minus_exact_matches_concat = [control[1], exp[1]]
                data_minus_exact_matches = pd.concat(data_minus_exact_matches_concat)  

                count += final_df.shape[0]

                print ("Caliper of {} has {} matches with {} matches total.".format(cal,final_df.shape[0], count))        


                
        else:
            print("Huzzah! All items have been matched.")
            walk = False
            break
    
    print ('This has taken {} minutes.'.format(round((time.time() - start)/60,5)))
        
    
    if walk:    
        walk, new_capiler = walk_request(previous_caliper, caliper)
        matches_df = fuzzy_match(data_minus_exact_matches, 
                    matches_df, 
                    group_col,
                    match_col, 
                    count,
                    start = time.time(),
                    previous_caliper = caliper, 
                    caliper = new_capiler, 
                    walk = walk)
        return matches_df
            
    else:
        return matches_df
            



def fuzzy_match_worker(control, exp, cal, match_col):
    #Create a dictionary that will hold the fuzzy matches temporarily
    fuzzy_matches = {}
    #Iterate through experimental/smaller group to find matches
    for count,m in enumerate(exp[1].index):

        #Create a pandas series that has all deltas between a single experimental val and all 
        dist = abs(exp[1][match_col].loc[m] - control[1][match_col])

        #Screening for smallest delta between control and experiment  
        if dist.min() <= cal:

            #Adding to existing dictionary
            fuzzy_matches[m] = dist.idxmin()

            #Dropping the matches from existing dataframe
            control[1].drop(dist.idxmin(), inplace = True)
            exp[1].drop(m, inplace = True)
            
    return fuzzy_matches



def build_clean_new_matches(fuzzy_matches):
    final_df = pd.DataFrame.from_dict(fuzzy_matches, orient = 'index')
    final_df.columns = ['Control']
    final_df['Experiment'] = final_df.index            
    final_df = final_df.drop_duplicates(subset = ['Control'])
    return final_df



def walk_request(previous_caliper, caliper):
    walk_req = input("Is that enough matches? y/n \n")
    
    if walk_req == 'y':
        new_caliper = 0
        walk = False
    elif walk_req == 'n':
        walk, new_caliper = caliper_request(previous_caliper, caliper)
    else:
        print('Please enter y or n. y will save matches to a csv and n will request a new caliper range')
        walk, new_caliper = walk_request(previous_caliper, caliper)

        
    return walk, new_caliper



def caliper_request(previous_caliper, caliper):
    new_caliper = input("Please enter a caliper. \nCurrent caliper range: {} to {}\n".format(str(previous_caliper), str(caliper)))
    try:        
        float(new_caliper)                  
        walk = True
        return walk, new_caliper
    except ValueError:
        print ("INPUT ERROR: Please enter a caliper of type float (decimal) such as .005")
        caliper_request()



def df_to_csv(matches_df, save_to_filename):
    print("Saving to csv at {}".format(save_to_filename))
    matches_df.to_csv(save_to_filename, index = False)



def static_vars():
    #Include double back slashes for filepath
    #if it's a csv converted from SPSS there is sometimes 
    #a dot (not a period) before the name ie. '﻿STATEID'. 
    #First try it without dot ie. 'STATEID'    
    source_file_path = ''
    id_col = ''
    group_col = ''
    match_col = ''    
    save_to_filename = ''
    return source_file_path, id_col, group_col, match_col, save_to_filename

if __name__ '__main__':
    begin()