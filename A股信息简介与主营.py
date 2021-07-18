# __*__endconding='utf-8'__*__
#信息采集于同花顺
import requests as req
import  pymysql
import time,json,sys
import tushare as ts
import pandas as pd
import prettytable as pt
import datetime
from dboprater import DB as db
configfile = './config/mysqlconfig.json'
file = './config/A股公司相关信息.csv'

###获取股票代码
def get_stocklist():
    tusharecode = db.get_config()
    pro = ts.pro_api(tusharecode['tushare'])
    stocklist=pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    stocklist=pd.DataFrame(stocklist)
    return stocklist

# 使用爱问财只要1个请求
def getstocksinfoFromaiwencai():
    datenow = datetime.datetime.now().strftime('%Y%m%d')
    stockfile = './config/A股公司相关信息.csv'
    stockinfo = []
    url = 'http://ai.iwencai.com/urp/v7/landing/getDataList'
    header = {
        'Host': 'ai.iwencai.com',
        'Connection': 'keep-alive',
        'Content-Length': '880',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://wap.iwencai.com',
        'Referer': 'http://wap.iwencai.com/',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'}
    postdata = {
        'query': '公司亮点与行业与主营业务与可比公司',
        'urp_sort_way': 'desc',
        'urp_sort_index': '最新涨跌幅',
        'page': '1',
        'perpage': '5000',
        'condition': '[{"chunkedResult":"公司亮点与行业与主营业务与可比公司","opName":"and","opProperty":"","sonSize":6,"relatedSize":0},{"indexName":"公司亮点","indexProperties":[],"source":"new_parser","type":"index","indexPropertiesMap":{},"reportType":"null","valueType":"_公司亮点","domain":"abs_股票领域","uiText":"公司亮点","sonSize":0,"queryText":"公司亮点","relatedSize":0,"tag":"公司亮点"},{"opName":"and","opProperty":"","sonSize":4,"relatedSize":0},{"indexName":"所属同花顺行业","indexProperties":[],"source":"new_parser","type":"index","indexPropertiesMap":{},"reportType":"null","valueType":"_所属同花顺行业","domain":"abs_股票领域","uiText":"所属同花顺行业","sonSize":0,"queryText":"所属同花顺行业","relatedSize":0,"tag":"所属同花顺行业"},{"opName":"and","opProperty":"","sonSize":2,"relatedSize":0},{"indexName":"主营产品名称","indexProperties":[],"source":"new_parser","type":"index","indexPropertiesMap":{},"reportType":"null","valueType":"_主营产品名称","domain":"abs_股票领域","uiText":"主营产品名称","sonSize":0,"queryText":"主营产品名称","relatedSize":0,"tag":"主营产品名称"},{"indexName":"财务维度可比公司","indexProperties":["nodate 1","交易日期 20201231"],"source":"new_parser","type":"index","indexPropertiesMap":{"交易日期":"20201231","nodate":"1"},"reportType":"YEAR","dateType":"报告期","valueType":"_最优可比公司","domain":"abs_股票领域","uiText":"财务维度可比公司","sonSize":0,"queryText":"财务维度可比公司","relatedSize":0,"tag":"财务维度可比公司"}]',
        'codelist': '',
        'indexnamelimit': '',
        'logid': 'c7c5c70a5c03f9f686d81b04a830ba4d',
        'ret': 'json_all',
        'sessionid': '6a765f385c2f1cfddd25c05a444fd6a9',
        'date_range[0]': '20201231',
        'iwc_token': '0ac9511916247088780837061',
        'urp_use_sort': '1',
        'user_id': '234319860',
        'uuids[0]': '24087',
        'query_type': 'stock',
        'comp_id': '5722297',
        'business_cat': 'soniu',
        'uuid': '24087'
    }
    content = None
    try:
        content = req.post(url=url, headers=header, data=postdata, timeout=120).json()
        # print(content)
    except BaseException as b:
        print('i wen cai request error', b)
        time.sleep(3)
        count = 0
        while count < 5:
            try:
                content = req.post(url=url, headers=header, data=postdata, timeout=120).json()
            except BaseException as b:
                time.sleep(2)
                continue
            if content != '':
                break
    if content['status_code'] != '0':
        return None
    jsondata = content['answer']['components'][0]['data']['datas']
    if jsondata is None:
        return None
    for tmpdata in jsondata:
        code = tmpdata['code']
        name = tmpdata['股票简称']
        market1=tmpdata['股票代码'][7:9]
        market='1'
        if market1=='SZ':
            market='0'
        tmpbank = str(tmpdata['所属同花顺行业']).split('-')
        bank = tmpbank[1]
        gailan=tmpdata['所属概念']
        gsld = tmpdata['公司亮点']
        if str(gsld) == 'None':
            gsld == ''
        zyfw=tmpdata['经营范围']
        zycpmc= tmpdata['主营产品名称']
        kbgs=''
        try:
            kbgs = tmpdata['财务维度可比公司']
        except BaseException as b:
            kbgs=''
        url=''
        try:
            url=tmpdata['公司网站']
        except BaseException as b:
            url=''
        str1 = str(code) + '$' + str(name) + '$' + str(market) + '$' + str(bank)+ '$' + str(gailan) + '$' + str(gsld) + '$' + str(zyfw)+ '$' + str(kbgs) + '$' + str(zycpmc) + '$' + str(url)
        print(str1)
        stockinfo.append(str1)

    with open(stockfile, 'w', encoding='utf-8') as fw:
        fw.write('代码$名称$市场代码$行业$概念$公司亮点$经营范围$可比公司$主营产品$URL' + '\n')
        for textvalue in stockinfo:
            fw.write(str(textvalue) + '\n')

#获取股票基本信息
def get_stockInfo(stocklist):
    sn = req.session()
    stockinfo = []  # 存储符合条件的企业
    # 同花顺的接口
    url = 'http://basic.10jqka.com.cn/mapp/%s/company_base_info.json'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'Cookie': 'searchGuide=sg; Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1=1608770907,1609917926,1610114215,1611192209; reviewJump=nojump; usersurvey=1; v=A-xOcNJfoJFX0bSt1GiqynybvcEdpZBLkkmkE0Yt-Bc6UYL3brVg3-JZdKSV',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'basic.10jqka.com.cn'
        }
    i = 0
    j = 0  # 符合条件记录数
    for line in stocklist.iterrows():
        code = line[1]['ts_code'][0:6]
        name = line[1]['name']
        industry = line[1]['industry']
        if industry is None or industry =='':
            industry=''
        url1 = url % code
        sn.headers = headers
        # pro = proxy.get_proxy()
        # print(pro)
        try:
            # sn.proxies=pro
            response=sn.get(url=url1)
            # jsoncontent = sn.get(url=url1, headers=headers).json()
        except BaseException:
            time.sleep(10)
            count=0
            while True:
                response=sn.get(url=url1)
                if response.status_code==200:
                    break
                else:
                    count+=1
                    print('获取%s股票信息 第 %s 次重试中！！！'%(name,count))
                    time.sleep(5)
                    if count>=5:
                        print('重试了%d 次仍失败，跳过！！！'%count)
                        break
        try:
            jsoncontent = response.json()
        except BaseException as e1:
            print('解释:%s 返回信息出错,跳过此股！！！' %name)
            continue

        # print(jsoncontent)
        time.sleep(1)  # 不休息会封IP
        stockdesc = jsoncontent['data']['describe']
        if stockdesc is None or stockdesc=='':
            stockdesc=''
        stockdesc=stockdesc.replace('\n','',-1)
        if len(stockdesc)>=100:
            stockdesc=stockdesc[0:100]
        base_business = jsoncontent['data']['base_business']
        if base_business is None or base_business=='':
            base_business = ''
        base_business=base_business.replace('\n','',-1)
        if len(base_business)>=300:
            base_business=base_business[0:300]
        business_scope = jsoncontent['data']['business_scope']
        if business_scope is None or business_scope=='':
            business_scope = ''
        business_scope=business_scope.replace('\n','',-1)
        if len(business_scope)>=300:
            business_scope=business_scope[0:300]
        try:
            str1 = code + '|' + name + '|' + industry + '|' + stockdesc+'|'+base_business+'|'+business_scope
            print(str1)
        except BaseException as e2:
            print(url1+'取值异常！')
        stockinfo.append(str1)


    with open(file, 'w', encoding='utf-8') as fw:
        fw.write('代码|名称|行业|简介|主营业务|业务范围' + '\n')
        for textvalue in stockinfo:
            fw.write(str(textvalue) + '\n')
    return stockinfo

def readstockinFile(file):
    infolists=[]
    f=open(file,'r',encoding='utf-8')
    context=f.readlines()
    for data in context:
        infolists.append(data)
    return infolists
# 将数据入表
def insertstockinfomation():
    filename = './config/A股公司相关信息.csv'
    #首先从通达信获取对象列表，并写文件

    pddata = pd.read_csv(filename,sep='$',error_bad_lines=False)
    pddata.drop_duplicates(keep="first", inplace=True)
    print(pddata.head())
    if pddata.empty:
        return
    sql = '''insert into stockinfo (code,name,market,bank,gainan,gsld,zyfw,kbgs,zycpmc,url) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
    conn = db.dbconnect()
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    '代码$名称$市场代码$行业$概念$公司亮点$经营范围$可比公司$主营产品$URL'
    for data in pddata.iterrows():
        code = data[1]['代码']
        code = str(code).rjust(6, '0')
        name = str(data[1]['名称'])
        market = str(data[1]['市场代码'])
        bank = str(data[1]['行业'])
        gailan = str(data[1]['概念'])
        zyfw = str(data[1]['经营范围'])
        gsld = str(data[1]['公司亮点'])
        kbgs = str(data[1]['可比公司'])
        zycpmc = str(data[1]['主营产品'])
        url = str(data[1]['URL'])
        values = (code, name, market,bank,gailan,gsld,zyfw,kbgs,zycpmc,url)
        # print(values)
        # break
        # print(values)
        try:
            cursor.execute(sql, values)
        except BaseException as b:
            print(b)
            continue
    conn.commit()
    cursor.close()
    conn.close()
    # except BaseException as b:
    #     pass

#######################根据条件查询mysql中的数据#######################
def select_stockinfos(condiction):
    tablename='stockinfomation'
    #dict=indb.file2dict(indb.configfile)  #读取配置信息
    conn=db.dbconnect()
    cursor= conn.cursor(cursor=pymysql.cursors.DictCursor)  #打开游标
    # condictions= str(condiction).strip('{').strip('}').replace(':','=',1).replace('\'','',2)

    sql = "select CODE, NAME, bank,gsld, zycpmc, ywfw from " + tablename + " where gsld like '%" + condiction + "%' ;"

    #print(sql)
    # print(sql)
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
    except BaseException as be:
        print(be)
        print("Error: unable to fetch data")
    cursor.close()
    if results is None:
        print('未查到数据！')
        return results
    else:
        # print('未查询到数据，请更新数据！')
        return results

def formatresults(results):
    #results   查询到的数据集
    #header   要输出的表头
    if results is None:
        print('无数据输出！！！')
        return

    header=['代码' , '名称', '行业' , '简介' , '主营业务' ]
    tb = pt.PrettyTable()
    tb.field_names=header #设置表头
    tb.align='l'  #对齐方式（c:居中，l居左，r:居右）
    for row in results:  # 依次获取每一行数据
        CODE = row['CODE']
        NAME = row['NAME']
        industry = row['industry']
        stockdesc = row['stockdesc']
        base_business = row['base_business']
        if len(base_business)>=40:
            base_business=base_business[0:40]
        business_scope = row['business_scope']
        tb.add_row([CODE, NAME, industry,stockdesc, base_business])
    # s=tb.get_html_string()  #获取html格式
    print(tb)

if __name__ == '__main__':
    cond=r"stockdesc like '%世界第一%'"
    var = sys.argv  # 可以接收从外部传入参数
    # 查个股概念信息，或某概念包含的股票信息
    try:
         infolist=select_stockinfos(var[1])
    except BaseException as e:
        print('未输入查询条件')
        exit(1)
    formatresults(infolist)


'''CREATE TABLE IF NOT EXISTS `stockinfomation`( 
CODE varchar(8),
NAME varchar(20),
industry varchar(100),
stockdesc varchar(100),  
base_business varchar(300),
business_scope varchar(300)
)ENGINE=InnoDB DEFAULT CHARSET=utf8;

create index stockinfomationcode on stockinfomation(CODE);
create index stockinfomationname on stockinfomation(NAME);
create index stockinfomationstockdesc on stockinfomation(stockdesc);'''

    # writetoFile(stockInfo,file)