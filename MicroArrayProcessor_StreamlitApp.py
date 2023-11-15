
import streamlit as st
import os
# import time
import numpy as np
import pandas as pd
import cv2
import imutils

from scipy import signal
from imutils import contours
from skimage import measure
from PIL import Image


class Slide_Process:
    def __init__(self):
        st.title("Slide Process Program")
        st.header("Use sidebar to pick files for processing")
        st.sidebar.header("1) Browse for files")
        self.dir_path = os.getcwd()+'/Data'
        
        file_options = [""] + [x for x in os.listdir(self.dir_path+"/Images") if ".tif" in x]
        self.file = st.sidebar.selectbox(".tif File", 
                      options=file_options)
        file_valid = self.file != ""
        # st.write(self.file2)
        # self.file = st.sidebar.file_uploader("Pick Image .tif file")
        map_options = [""] + [x for x in os.listdir(self.dir_path+"/InfoDocs") if "map" in x]
        self.map_file = st.sidebar.selectbox("Map File", 
                     options=map_options)
        map_valid = self.map_file != ""
        
        id_options = [""] + [x for x in os.listdir(self.dir_path+"/InfoDocs") if "IDs" in x]
        self.ID_file = st.sidebar.selectbox("ID File", 
                     options=id_options)
        id_valid = self.ID_file != ""

        col1, col2 = st.columns(2)
        with col1:
            self.threshold_ratio = st.number_input("Set ratio of signal to background threshold", 
                                                   value=1.5, min_value=0.9, max_value=20.0, step=0.01)
            self.pixelThresh = st.number_input("Set pixels for minumim feature size (usually 50)", 
                                               value=50, min_value=10, max_value=250,step=10)
            self.dot_pitch = st.number_input("Calculated pixels between features (usually 45 or 50)", 
                                               value=45, min_value=30, max_value=60,step=5)
            
        with col2:
            self.minRadius = st.number_input("Set min feature radius (usually 5)", 
                                             value=5, min_value=1, max_value=10,step=1)
            self.maxRadius = st.number_input("Set max feature radius (usually 25)", 
                                             value=25, min_value=10, max_value=100,step=1)
        st.write("Once files are defined, click image processing button")
        st.write("Once finished, click data processing button")
        st.subheader("Progress Bar")
        self.prog_bar = st.progress(0)
        if all([map_valid, id_valid, file_valid]):
            # self.modules["styler"].writeStyled("Progress Bar", font_key="large_RoyalBlue")
            # st.write(self.dir_path + "/InfoDocs/" + self.map_file)
            self.map_df = pd.read_csv(self.dir_path + "/InfoDocs/" + self.map_file, header=None)
            self.map_df = self.map_df.fillna(0)
            self.ID_df = pd.read_csv(self.dir_path + "/InfoDocs/" + self.ID_file)
            
            self.output_data = []
            st.sidebar.header("2) Click to run image process")
            if st.sidebar.button("Run Image Process"):
                st.write("Make sure the boundary in green is outlining the microarray in each well",
                         unsafe_allow_html=True)
                self.import_file()
                self.data_output_process()
                
            data_path = self.dir_path + "/OutputFiles/" + self.file[:-4] + '_OutputFile.csv'
            if os.path.exists(data_path):
                self.data_df = pd.read_csv(self.dir_path + "/OutputFiles/" + self.file[:-4] + '_OutputFile.csv')
                self.data_df = self.data_df.fillna(0)
                st.sidebar.header("3) Click to run data process")
                if st.sidebar.button("Run Data Process"):
                    self.process_data()
                    self.prog_bar.progress(100)
                    self.data_output_process_Final()
    
    def import_file(self):
        # cv2.imread is the line that takes the longest time (~ 5-6 seconds)
        im_cv2_whole = cv2.imread(self.dir_path+"/Images/"+self.file) ####
        ############
        im = Image.open(self.dir_path+"/Images/"+self.file)
        imarray_whole = np.array(im)
        xlen = im.size[0]
        self.xwell_size = round(xlen/3)
        ylen = im.size[1]
        self.ywell_size = round(ylen/8)
        # st.write(im)
        self.iterate_over_wells(imarray_whole,im_cv2_whole)
        
    # Function to iterate through the 21 wells
    def iterate_over_wells(self, imarray_whole, im_cv2_whole):
        col1, col2, col3 = st.columns(3)
        columns = [col1, col2, col3]
        well_num = 0
        well_lst = []
        for i in range(3): # 3
            with columns[i]:
                for j in range(7): # 7
                    well_num +=1
                    self.prog_bar.progress((well_num/21))
                    # iterate through the image in the sub arrays
                    imarray_well = imarray_whole[self.ywell_size*(j):self.ywell_size*(j+1), 
                                            self.xwell_size*(i):self.xwell_size*(i+1)]
                    im_cv2_well = im_cv2_whole[self.ywell_size*(j):self.ywell_size*(j+1), 
                                          self.xwell_size*(i):self.xwell_size*(i+1)]
                    well_lst.append(imarray_well)
                    self.process_well(imarray_well,im_cv2_well,well_num)
                    
        for image in well_lst:
            pass
        
    def process_well(self, im_array, im_cv2, well_num):
        
        # Threshold the image to find values that are high and eorde and dilate
        median_background = np.median(im_array)
        thresh = cv2.threshold(im_array, median_background*self.threshold_ratio, 
                               65536, cv2.THRESH_BINARY)[1]
        # thresh = cv2.adaptiveThreshold(im_array, 65536, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       # cv2.THRESH_BINARY,11,2)
        thresh = cv2.erode(thresh, None, iterations=2)
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Create labels and a mask from the threshold high parts
        labels = measure.label(thresh, background=0)
        mask = np.zeros(thresh.shape, dtype="uint8")
        # loop over the unique components
        for label in np.unique(labels):
            # if this is the background label, ignore it
            if label == 0:
                continue
            # otherwise, construct the label mask and count the number of pixels 
            labelMask = np.zeros(thresh.shape, dtype="uint8")
            labelMask[labels == label] = 255
            numPixels = cv2.countNonZero(labelMask)
            # if the number of pixels in the component is sufficiently large, then add it to our mask 
            if numPixels > self.pixelThresh:
                mask = cv2.add(mask, labelMask)

        # find the contours in the mask, then sort them from left to right
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = contours.sort_contours(cnts)[0]
        
        # loop over the contours
        count = 0
        lst_cX = []
        lst_cY = []
        lst_sumsq = []
        lst_intens = []
        x_origin, y_origin, x_high, y_high = self.find_origin(im_array, self.map_df.shape[1]-1, self.map_df.shape[0]-1)
        # Set bounding limits for the features
        buffer = 12
        x_low = x_origin - buffer
        x_high = x_high + buffer
        y_low = y_origin - buffer
        y_high = y_high + buffer

        # sub_array = im_array[x_low:x_high, y_low:y_high]
        # mean_background = round(np.mean(sub_array[sub_array < 1000]),4)
        # median_background2 = round(np.median(sub_array[sub_array < 1000]),4)
        
        #Put well number and background value on the image
        cv2.putText(im_cv2, "{}".format(well_num), (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 0), 4)
        cv2.putText(im_cv2, "Background Median = " "{}".format(median_background), (25, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        # cv2.putText(im_cv2, "Background Mean = " "{}".format(median_background2), (25, 160),
        #             cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        for (i, c) in enumerate(cnts):
            # draw the bright spot on the image
            (x, y, w, h) = cv2.boundingRect(c)
            # cX and cY are the centerpoints that are used for getting intensty values
            ((cX, cY), radius) = cv2.minEnclosingCircle(c)
            cv2.circle(im_cv2, (int(cX), int(cY)), int(radius),(255, 0, 0), 1)
            
            #Draw a rectangle for boundries
            cv2.rectangle(im_cv2, (x_low, y_low), (x_high, y_high),(0, 255, 0),2)
            #draw the contour circel on the image and place text for numbering
            if (cX > x_low and cX < x_high and cY > y_low and cY < y_high 
                and radius>self.minRadius and radius<self.maxRadius):
                cv2.circle(im_cv2, (int(cX), int(cY)), int(radius),(0, 255, 255), 1)
                lst_cX.append(int(cX))
                lst_cY.append(int(cY))
                lst_sumsq.append(np.sqrt(int(cX)**2 + int(cY)**2))
                cv2.putText(im_cv2, "{}".format(count + 1), (x+5, y-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 1)
                value_list = []
                # set area that will be averaged together for the intesnity values
                radius_to_avg = round(radius/2)
                for k in range(radius_to_avg):
                    for j in range(radius_to_avg):
                        # force are to bea circle though pythag theorem
                        if np.sqrt(k^2 + j^2) < radius_to_avg:
                            value_list.append(im_array[int(cY)+j,int(cX)+k])
                            value_list.append(im_array[int(cY)-j,int(cX)-k])
                # average the values together to final value
                avg_intensity = np.mean(value_list)
                # create list of intensities
                lst_intens.append(avg_intensity)
                cv2.putText(im_cv2, "{}".format(count + 1) + " - " + str(round(avg_intensity,2)), 
                            #+  " (r = "+str(int(radius))+")", 
                            (20, 160+count*20),cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                            (255, 255, 255), 1)
                count+=1
        # set the origin index with the min of the root of the squares
        min_index = lst_sumsq.index(min(lst_sumsq))
        self.output_file_create(min_index, lst_cX, lst_cY, lst_intens, median_background)
        st.image(im_cv2*1000, caption="Well #"+str(well_num), clamp=True)
        
    def find_origin(self, im_array, x_len, y_len):
        # im_array_crop = im_array[int(self.xwell_size*0.1):int(self.xwell_size*0.9), int(self.ywell_size*0.1):int(self.ywell_size*0.9)]
        gauss = []
        mu = 16
        sigma = 5
        for x in range(31):
            gauss.append((1/(mu*np.sqrt(2*np.pi))) * np.exp(-(1/2)*((x-mu)/(sigma))**2)*20000000)
        sum_row = np.sum(im_array,axis=0)
        sum_col = np.sum(im_array,axis=1)
        x_test = [0]*800
        y_test = [0]*800
        start = 0
        for peak_x in range(x_len):
            for x in range(len(gauss)):
                x_test[start + x + (peak_x*int(self.dot_pitch))] = gauss[x]
        for peak_y in range(y_len):
            for y in range(len(gauss)):
                y_test[start + y + (peak_y*int(self.dot_pitch))] = gauss[y]
    
        conv_x = signal.convolve(x_test, np.flip(sum_row), mode='full', method='fft')
        conv_y = signal.convolve(y_test, np.flip(sum_col), mode='full', method='fft')
        
        conv_x_max = np.where(conv_x == max(conv_x))
        x_origin = int(len(sum_row)-conv_x_max[0]+mu)
        
        conv_y_max = np.where(conv_y == max(conv_y))
        y_origin = int(len(sum_col)-conv_y_max[0]+mu)
        # st.write(x_origin, y_origin)

        x_high = x_origin+(self.dot_pitch*(x_len))
        y_high = y_origin+(self.dot_pitch*(y_len))
        
        return x_origin, y_origin, x_high, y_high

    def output_file_create(self, origin_idx, lst_cX, lst_cY, lst_intens, background):
        # set origin x and y values
        x_origin = lst_cX[origin_idx]
        y_origin = lst_cY[origin_idx]
        # print(x_origin, y_origin)
        # Set origin to zero and subtract from others and set to integers as well
        for i in range(len(lst_cX)):
            lst_cX[i] = round((lst_cX[i]- x_origin)/self.dot_pitch)
            lst_cY[i] = round((lst_cY[i]- y_origin)/self.dot_pitch)
        # make a few lists for the output files 
        back_lst = [(self.threshold_ratio*background)]*len(lst_cX)
        self.output_data.append(lst_cX)
        self.output_data.append(lst_cY)
        self.output_data.append(lst_intens)
        self.output_data.append(back_lst)

    def data_output_process(self):
        # make output file from lists into a dataframe
        output_df = pd.DataFrame(self.output_data)
        output_df = output_df.T
        os.makedirs(self.dir_path + '/OutputFiles', exist_ok=True) 
        output_df.to_csv(self.dir_path + '/OutputFiles/' + self.file[:-4] + '_OutputFile.csv') 

        
    def process_data(self):
        output_file = []
        probe_list = ['Probe_ID', 0]
        # HPA_ID_lst =[]
        for i in range(21):
            output_dict = {}
            # probes = []
            rfu_vals = []
            x_index = self.data_df[str(0+(i*4))]
            y_index = self.data_df[str(1+(i*4))]
            intensity = self.data_df[str(2+(i*4))]
            back_val = self.data_df[str(3+(i*4))]
            temp_list = []

            for j in range(len(x_index)):
                if (x_index[j] < (self.map_df.shape[1]-1) and x_index[j] >= 0 
                    and y_index[j] < self.map_df.shape[0] and y_index[j] >= 0):
                    
                    key_probe = int(self.map_df[round(x_index[j])+1][y_index[j]])
                    if key_probe in output_dict:
                        output_dict[key_probe].append(intensity[j])
                    else:
                        output_dict[key_probe] = [0]
                        output_dict[key_probe].append(intensity[j])
                    if key_probe in probe_list:
                        pass
                    else:
                        probe_list.append(key_probe)
                        
                temp_list = [0] * len(probe_list)   
                temp_list[0] = ('Well ' + str(i+1))
            
            for key in output_dict:
                if len(output_dict[key]) > 2:
                    output_dict[key] = np.mean(output_dict[key][1:])
                    rfu_vals.append(round(output_dict[key],3))
                    temp_list[probe_list.index(key)] = round(output_dict[key],3)
                temp_list[probe_list.index(0)] = back_val[0]
            if i == 0:
                output_file.append(probe_list)

            output_file.append(temp_list)  
            
        output_file.insert(1,[0]*len(output_file[0]))

        for k in range(len(output_file[0])):
            if k == 0:
                output_file[1][k] = "Sample_ID"
            else:
                ID_index = list(self.ID_df['Cap_ID']).index(output_file[0][k])

                output_file[1][k] = self.ID_df['Sample_ID'][ID_index]

               
        self.output_df = pd.DataFrame(output_file).T
        self.output_df.fillna(0, inplace=True)
        for i in range(22):
            # print(self.output_df[(i+1)])
            self.output_df[(i+1)] = self.output_df[(i+1)].replace(0, self.output_df[(i+1)][1])
            
        headers = self.output_df.iloc[0]
        self.output_df.columns = headers
        self.output_df.drop(index=self.output_df.index[0], axis=0, inplace=True)
        self.output_df.sort_values(by=['Probe_ID'], axis=0, ascending=True, inplace=True)
        # st.write(headers)
        st.write(self.output_df)
        
    def data_output_process_Final(self):
        self.output_df.to_csv(self.dir_path + '/OutputFiles/'+ 'FinalOutputValues_' 
                              + self.file[:-4] + '.csv')  


if __name__== "__main__":
    Slide_Process()


"""
2023-01-02 Version 

@author: abremner
"""
