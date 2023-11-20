# Micro Array Processor
Streamlit App that take the input of a raw .tif image file from a slide scanner with 21 microarrays and processes them to output the intesities of the features using an input map and ID key to sort and average replicate features.

Below are example imaged of the raw .tif image file from the slide scanner, then one zoomed in well to show the mocro array and fianllay the processed microarray with the featured circles and picked out.
<table>
    <tr>
    <td style="text-align:center">Whole slide</td>
    <td style="text-align:center">One microarray</td>
    <td style="text-align:center">Processed microarray</td>
  </tr>
  <tr>
    <td>
      <img src="ReadMeImages/Whole_Slide.png" alt="Whole slide Image" height="300" title="Whole slide Image">
    </td>
    <td>
      <img src="ReadMeImages/Raw_Well_Image.png" alt="One microarray Image" height="300" title="One microarray Image">
    </td>
    <td>
      <img src="ReadMeImages/Processed_Well_Image.png" alt="Processed microarray Image" height="300" title="Processed microarray Image">
    </td>
  </tr>
</table>

## App Overview
The app can be run from the command line with "streamlit run MicroArrayProcessor_StreamlitApp.py" which then open in a browser.
