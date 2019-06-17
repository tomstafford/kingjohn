'''
python script for 
- parsing data for King John's itenary 1199-1216
- creating map images
- putting these into a gif 
'''


'''
DEPENDENCIES
- created on Ubuntu linus 14.06
- assumes bash environment & ffmpeg for making gif
- python assumes conda environment contained in mapping.yml
'''

import pandas as pd #dataframes
import os #file and folder functions
import numpy as np
import datetime
import matplotlib.pyplot as plt #plotting function
import cartopy.crs as ccrs
import cartopy
import cartopy.feature as cfeature

#os.chdir('/home/tom/t.stafford@sheffield.ac.uk/A_UNIVERSITY/toys/kingjohn2')

#load data
df=pd.read_json('Itinerary.js')

#extract essential fields
#place,lat,lon,arr,dep
df['place']=df['events'].apply(lambda x: x['mapKey'])
df['lat']=df['events'].apply(lambda x: x['LatLong'][0] if x['LatLong'] else np.NaN)
df['lon']=df['events'].apply(lambda x: x['LatLong'][1] if x['LatLong'] else np.NaN)
df['arr']=df['events'].apply(lambda x: x['start'] if x['start'] else np.NaN)
df['dep']=df['events'].apply(lambda x: x['end'] if 'end' in x else np.NaN)

#calculate dwell time if there is an explicit departure date
def getdats(row):
    try:
        #return (pd.to_datetime(row['arr'],format='%d/%m/%Y',errors='ignore')-pd.to_datetime(row['dep'],format='%d/%m/%Y',errors='ignore'))
        return datetime.datetime.strptime(row['dep'], '%Y-%m-%d')-datetime.datetime.strptime(row['arr'], '%Y-%m-%d')
    except:
        return np.NaN

df['dwell']=df.apply(getdats,axis=1).dt.days


#tidy up
df.drop('events',axis=1,inplace=True) #drop original import single column
df.sort_values('arr',inplace=True) #arrange by arrival date
df['seq']=range(len(df)) #explicitly label sequence of itinery, in case we rearrange df later

#calculate departure date from arrival date at next place, less one day
df['arr-1']=df['arr'].shift(-1) #make arrival at next place explicit as new column
df['dep-1']=df['arr-1'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d')-datetime.timedelta(days=1) if pd.notnull(x) else np.NaN) #calculate arrival at next place less one day

df['dwell2']=df['dep-1']-df['arr'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d'))

df['dwell2']=df['dwell2'].apply(lambda x: x.days) #convert to int


'''
--------------------------> MAKING A MAP
'''
# Cribbing from
# https://uoftcoders.github.io/studyGroup/lessons/python/cartography/lesson/
# and
# https://matthewkudija.com/blog/2018/04/21/travel-map-cartopy/




def new_base(df):
    plt.clf()
    # map boundaries

    vert_buffer=(df.lat.max()-df.lat.min())*0.05
    horz_buffer=(df.lon.max()-df.lon.min())*0.05
    top = df.lat.max()+vert_buffer
    bottom = df.lat.min()-vert_buffer
    left = df.lon.min()-horz_buffer
    right = df.lon.max()-horz_buffer
    
        
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # [lon_min, lon_max, lat_min, lat_max]
    ax.set_extent([left, right, bottom, top], crs=ccrs.PlateCarree())
    
    # add and color high-resolution land
    OCEAN_highres = cfeature.NaturalEarthFeature('physical', 'ocean', '50m',
                                                 edgecolor='#B1B2B',
                                                 facecolor='white',
                                                 linewidth=.1
                                                 )
    
    ax.add_feature(OCEAN_highres, zorder=0,
                   edgecolor='#B1B2B4', facecolor='#7f7f7f')
    
    


markparam = 14
year=0

from matplotlib import colors as mcolors
colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
our_colors=['seagreen','yellowgreen','skyblue','sandybrown','salmon','limegreen','lightpink','fuchsia','lightskyblue','lavender','khaki','indigo','hotpink','green','gold','brown','cadetblue','mistyrose']
colorbase=1199

xpos=[0.05]*10+[0.2]*10
ypos=np.arange(0.4,0.1,-0.03)

'''
--------------------------> ADDING ITINERARY DETAILS
'''

new_base(df)

for index, row in df.iterrows():
    if index < 63000:
        '''
        if row['dwell2'] > 1:
            annotext = row['place'] + '\n' + row['arr'] + '\n - ' + row['arr-1']
        else:
            annotext = row['place'] + '\n' + row['arr'] + '\n ' + ' '
        '''
        lastyear=year
        year=int(row['arr'][:4])       
        try:
            nextyear=int(df.iloc[index+1]['arr'][:4])
        except:
            nextyear=1217
            print('1217')
                
        
        colorname='blue' #our_colors[(year-11)%18]
        
        filename = 'frames/' + str(row['seq']).rjust(4, '0') + '.png'

        marksize = markparam * np.log(row['dwell'] + 0.5)
            
        plt.plot(row['lon'], row['lat'], '.', alpha=0.15, ms=marksize, color=colorname)
        
        if (not nextyear==year):
            annotext=str(year)
            ann = plt.annotate(annotext, xy=(xpos[(year-11)%18], ypos[(year+1)%10]),xycoords='axes fraction',color=colorname)
            plt.savefig(filename,dpi=160,bbox_inches='tight')
            ann.remove()
            new_base(df)
                                
        # plt.title(annotext)
        # plt.ylim([46,56])
        # plt.xlim([-4,2])
        
    
'''
--------------------------> ANIMATING
'''

# combine frames into gif
if True:
    os.system('convert -delay 130 frames/*.png animated_itinerary3.gif')
