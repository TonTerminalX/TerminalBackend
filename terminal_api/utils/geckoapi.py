import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc


import requests


class GeckoTerminalApi:
    api_url = "https://api.geckoterminal.com/api/v2"
    get_ohlcv_data_endpoint = "/networks/{network}/pools/{pool}/ohlcv/day"

    headers = {
        "Accept": "application/json;version=20230302"
    }

    @classmethod
    def get_ohlcv_data(cls, pool_address: str):
        formater_endpoint = cls.get_ohlcv_data_endpoint.format(network="ton", pool=pool_address)
        response = requests.get(cls.api_url + formater_endpoint, headers=cls.headers, timeout=(10, 10))
        response.raise_for_status()
        return response.json()["data"]["attributes"]["ohlcv_list"]


if __name__ == "__main__":
    api = GeckoTerminalApi()
    chart = api.get_ohlcv_data("EQBCwe_IObXA4Mt3RbcHil2s4-v4YQS3wUDt1-DvZOceeMGO")

    ohlc = [
        [
            mdates.date2num(datetime.datetime.utcfromtimestamp(item[0])),
            item[1],  # Open
            item[2],  # High
            item[3],  # Low
            item[4],  # Close
        ]
        for item in chart
    ]

    volume = [item[5] for item in chart]
    dates = [mdates.date2num(datetime.datetime.utcfromtimestamp(item[0])) for item in chart]
    colors = ['g' if ohlc[i][4] >= ohlc[i][1] else 'r' for i in range(len(ohlc))]  # Цвета для объёмов

    # Построение графика
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

    # Свечной график
    ax1.xaxis_date()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    candlestick_ohlc(ax1, ohlc, width=0.6, colorup='g', colordown='r', alpha=0.8)
    ax1.set_title("Candlestick Chart with Volume")
    ax1.set_ylabel("Price")
    ax1.grid()

    # Объём
    ax2.bar(dates, volume, color=colors, width=0.6, alpha=0.8)
    ax2.set_ylabel("Volume")
    ax2.grid()

    # Общая настройка
    plt.xlabel("Date")
    plt.tight_layout()
    plt.show()

