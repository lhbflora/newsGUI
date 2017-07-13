'''

author: Flora_Lin
NewsCrawler and Analyzer
Crawling the news today and display in the GUI              #used module: wxPython, selenium, PhantomJS, BeautifulSoup
Reach the news page on the GUI directly
Extract the hottest area or country and make a bar chart    #used module: matplotlib,collections, pandas
Extract the hottest words and create a wordcloud            #used module: jieba, wordcloud

'''
import time
import matplotlib.pyplot as plt
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import wx
#import _thread as thread
import jieba.posseg as pseg
from os import path
from scipy.misc import imread
from wordcloud import WordCloud, ImageColorGenerator
import collections
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FormatStrFormatter

ID_EVENT_RELOAD = 9999
driver = webdriver.PhantomJS()  #using PhantomJS to parse the JS webpage
url = 'http://news.163.com/world/'



class NewsGUI(wx.Frame):
    option_list = {'No.':True, 'Title': True, 'Time': True}


    """docstring for NewsGUI."""
    def __init__(self, title):
        wx.Frame.__init__(self,None,title = title,size = (450,600))

        #set a Munu Bar on the top
        self.CreateStatusBar()
        menuBar = wx.MenuBar()
        filemenu = wx.Menu()
        menuBar.Append(filemenu,"&File")
        menureload = filemenu.Append(ID_EVENT_RELOAD,"&Reload","Reload articles")
        self.Bind(wx.EVT_MENU,self.OnReload,menureload)
        menuQuit = filemenu.Append(wx.ID_EXIT,"Q&uit","Terminate the program")
        self.Bind(wx.EVT_MENU,self.OnQuit,menuQuit)
        self.SetMenuBar(menuBar)

        #set a BoxSizer
        panel = wx.Panel(self)

        TextSizer = wx.BoxSizer(wx.HORIZONTAL)
        labelText = wx.StaticText(panel,label = "Hottest Areas Number: ")
        TextSizer.Add(labelText,0,wx.ALIGN_BOTTOM)


        search_text = wx.TextCtrl(panel, value = "10", style = wx.TE_PROCESS_ENTER)
        TextSizer.Add(search_text)
        self.num = int(search_text.GetValue())

        search_btn = wx.Button(panel, label = "Hot Areas")
        TextSizer.Add(search_btn)
        self.Bind(wx.EVT_BUTTON, self.OnClickSearch, search_btn)    #search for the most popular areas and countries

        cloud_btn = wx.Button(panel, label = "Hot Words")
        TextSizer.Add(cloud_btn)
        self.Bind(wx.EVT_BUTTON, self.OnClickCloud, cloud_btn)

        self.list = wx.ListCtrl(panel, wx.NewId(), style = wx.LC_REPORT, size = (-1,-1))
        self.CreateHeader()

        pos = self.list.InsertItem(0,"loading..")
        self.list.SetItem(pos,1,"--")
        self.list.SetItem(pos,2,"--")
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDoubleClick, self.list)  #Double click to reach the news page

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(TextSizer, 0, wx.ALL, 5)
        sizer.Add(self.list, wx.ALL | wx.EXPAND, 5)
        panel.SetSizerAndFit(sizer)
        self.Center()
        self.FetchContent(url)

    def CreateHeader(self):
        self.list.InsertColumn(0,'No.')
        self.list.InsertColumn(1, "Title")
        self.list.InsertColumn(2, "Time")


    def setData(self, datadf):
        self.list.ClearAll()
        self.CreateHeader()
        pos = 0
        for col in range(len(datadf)):
            pos = self.list.InsertItem(index = pos + 1, label = str(col+1))
            self.list.SetColumnWidth(0, -1)
            self.list.SetItem(index = pos, column = 1, label = datadf.loc[col,'title'])
            self.list.SetColumnWidth(1, -1)
            self.list.SetItem(index = pos, column = 2, label = datadf.loc[col,'time'])
            if (pos % 2 == 0):
            # Set new look and feel for odd lines
                self.list.SetItemBackgroundColour(pos, (134, 225, 249))

    def FetchContent(self,rurl):
        print('Fetching url: '+rurl+'.......')
        driver.get(rurl)
        markup = driver.page_source   #Parse taget page source

        self.scroll_down(driver = driver, times = 3)
        pattern = BeautifulSoup(markup, 'lxml')
        time.sleep(3)
        all_title = BeautifulSoup(markup, 'lxml').find_all('div', class_='news_title')  #Extract the source code to extract title, time and address
        time_stamp_list = pattern.find_all('span', class_= 'time')
        title_list = []
        time_list = []

        for item in time_stamp_list:
            time_stamp = item.string
            time_list.append(time_stamp)

        for item in all_title:
            title = item.a.string
            address = item.a.get('href')
            title_list.append({'title':title,'address':address})
        source_df = pd.DataFrame(title_list)
        source_df['time'] = time_list
        source_csv = source_df.to_csv('News.csv')
        self.retrieve_articles()
        print('Fetching completed')

    def scroll_down(self,driver,times):
        for i in range(times):
            print('scrolling {}th time'.format(i+1))
            time.sleep(4)
            driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")

    def OnReload(self,event):
        # thread.start_new_thread(self.FetchContent(url),())
        self.FetchContent(url)

    def OnQuit(self,event):
        self.Close()
        self.Destroy()

    def OnClickSearch(self,event):
        #extract words whose flag means the name of countries and areas
        #sort the areas by frequency and display the bar chart of statistical data
        font = FontProperties(fname=r"c:\windows\fonts\simsun.ttc", size=14)
        with open('title.txt','r',encoding = 'gbk') as f:
            title_text = f.readlines()
        #stop_words = set(line.strip() for line in open('stopwords.txt', encoding='utf-8'))
        titlelist = []
        for subject in title_text:
            if subject.isspace():
                continue
            word_list = pseg.cut(subject)
            for word,flag in word_list:
                if flag in ('ns','nt'):
                    titlelist.append(word)
        counter = collections.Counter(titlelist)
        countrydf = pd.DataFrame()
        countrydf['country'] = counter.keys()
        countrydf['freq'] = counter.values()
        countrydf = countrydf.sort_values('freq',ascending=False)
        top_ten = countrydf.iloc[:self.num]
        other_freq = countrydf.iloc[self.num:30].freq.sum()
        otherdf = pd.DataFrame({'country':pd.Series({1: 'others'}),
                        "freq": pd.Series({1:other_freq})})
        result = pd.concat([top_ten,otherdf], ignore_index=True)
        result = result.set_index(['country'])
        fig = result.plot(kind = 'bar')
        for label in fig.get_xticklabels() :
            label.set_fontproperties(font)
        ymajorFormatter = FormatStrFormatter('%d') #设置y轴标签文本的格式
        fig.yaxis.set_major_formatter(ymajorFormatter)
        fig.set_title('Hot Areas')
        fig.set_xlabel("Areas")
        fig.set_ylabel("Frequency")
        plt.show()



    def retrieve_title(self):
        source_df = pd.read_csv('News.csv',encoding='gbk')
        titlelist = []
        for i in range(len(source_df)):
            title = source_df.loc[i,'title']
            titlelist.append(title)
            title_text = ''.join(titlelist)
        with open('title.txt','w') as f:
            f.writelines(title_text)
        # return title_text

    def OnClickCloud(self,event):
        #create wordcloud and show the data in the color of the mask image 
        self.retrieve_title()
        with open('title.txt','r',encoding = 'gbk') as f:
            title_text = f.readlines()
        stop_words = set(line.strip() for line in open('stopwords.txt', encoding='utf-8'))
        titlelist = []
        for subject in title_text:
            # if subject.isspace():
            #     continue
            word_list = pseg.cut(subject)
            for word,flag in word_list:
                if not word in stop_words:
                    titlelist.append(word)
        d = path.dirname(__file__)
        mask_image = imread(path.join(d,"mickey.png"))
        content = ' '.join(titlelist) # all 'n' words in the news title


        wordcloud = WordCloud(font_path='simhei.ttf', background_color="white",mask=mask_image, max_words=40).generate(content)
        #Display the generated image:
        image_colors = ImageColorGenerator(mask_image)
        plt.imshow(wordcloud.recolor(color_func = image_colors))
        plt.axis("off")
        plt.show()
        wordcloud.to_file(path.join(d,'wordcloud.jpg'))


    def OnDoubleClick(self,event):
        source_df = pd.read_csv('News.csv',encoding='gbk')
        title_text = event.GetText()
        address = source_df.loc[int(title_text)-1,'address']
        Chromedriver = webdriver.Chrome(r'E:\software\anaconda\Lib\site-packages\selenium\webdriver\chromedriver.exe')
        Chromedriver.get(address)

    def retrieve_articles(self):
        source_df = pd.read_csv('News.csv',encoding='gbk')
        self.setData(source_df)

if __name__ == '__main__':
    app = wx.App(False)
    Blog = NewsGUI("Today News")
    Blog.Show(True)
    app.MainLoop()
