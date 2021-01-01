app.component('data-plot', {
    template:
    /*html*/
`
<div class="chart-container" style="position: relative; height:75%;">
    <canvas id="analog"></canvas>
</div>
`,
    props: {
        sensor_data: {
            // type: Object,
            required: true
        }
    },
    data() {
        return {
            sensorDataChart: null
        }
    },
    methods: {
        /////////////////////////////////////
        // UTILITY FUNCTIONS

        // Compute a string with min/max/average on the given array of (x, y) points
        computeStats(sampleArray) {
            var minY = Number.MAX_SAFE_INTEGER, maxY = 0, avgY = 0;       
            var prevX = 0;
            sampleArray.forEach(function (point, index) {
                if (point.y < minY){
                    minY = point.y;
                }
                if (point.y > maxY) {
                    maxY = point.y;
                }
                if (prevX > 0) {
                    avgY = avgY + point.y * (point.x - prevX); // avg is weighted: samples with a longer period weight more
                }
                prevX = point.x;
            });
            avgY = avgY / (prevX - sampleArray[0].x);
            return "min: " + minY + ", max: " + maxY + ", avg: " + Math.floor(avgY);
        },
        plotData(sensorData) {
            // Response is e.g.: {"0": [{"time": 1608415319, "temperature": 69, "humidity": 40},
            //                          {"time": 1608415379, "temperature": 70, "humidity": 39}],
            //                    "1": [{"time": 1608415319, "temperature": 70, "humidity": 41},
            //                          {"time": 1608415379, "temperature": 69, "humidity": 42}]}
   
            var maxSamples = Math.floor(parseFloat(document.getElementById("maxSamplesField").value) * 60);
    
            var nowSec = Math.round(Date.now() / 1000);
            var oldestTime = nowSec - maxSamples * 60;
    
            if (maxSamples <= 360) {
                this.sensorDataChart.options.scales.xAxes[0].time.stepSize = 15;
            } else if (maxSamples <= 720) {
                this.sensorDataChart.options.scales.xAxes[0].time.stepSize = 30;
            } else {
                this.sensorDataChart.options.scales.xAxes[0].time.stepSize = 60;
            }
            
            // Add point to analog chart
            // check if the property/key is defined in the object itself, not in parent
            for (stationId in this.sensor_data) {
                if (this.sensor_data.hasOwnProperty(stationId)) {
                    stationId = parseInt(stationId);
                    sensorData = this.sensor_data[stationId]
                    this.sensorDataChart.data.datasets[stationId].data = []
                    for (var i = 0; i < sensorData.length; i++) {
                        dataPoint = sensorData[i]
                        if (dataPoint.time < oldestTime) {
                            continue;
                        }
                        data = this.sensorDataChart.data.datasets[stationId].data;
                        data.push({x: new Date(parseInt(dataPoint.time) * 1000), y: parseFloat(dataPoint.temperature)});
                        // Limit its length to maxSamples
                        data.splice(0, data.length - maxSamples);
                    }
                }
            }
    
            // Put stats in chart title
            this.sensorDataChart.options.title.text = "Station Temperatures - use mouse wheel or pinch to zoom";
            // Remember smallest X
            var minX = data[0].x;
            
    
            this.sensorDataChart.update();
        }
    },
    mounted() {
        this.sensorDataChart = new Chart(document.getElementById('analog'), {
            // The type of chart we want to create
            type: 'scatter',
        
            // The data for our dataset
            data: {
              datasets: [{
                label: 'Station 0',
                backgroundColor: 'rgb(0,0,0,0)',
                borderColor: 'rgb(255, 99, 132)',
                data: [],
                showLine:true
              },
              {
                label: 'Station 1',
                backgroundColor: 'rgb(0,0,0,0)',
                borderColor: 'rgb(99, 255, 132)',
                data: [],
                showLine:true
              },
              {
                label: 'Station 2',
                backgroundColor: 'rgb(0,0,0,0)',
                borderColor: 'rgb(99, 132, 255)',
                data: [],
                showLine:true
              },
              {
                label: 'Thermostat State',
                backgroundColor: 'rgb(0,0,0,0)',
                borderColor: 'rgb(63, 63, 63)',
                data: [],
                showLine:true,
                cubicInterpolationMode: 'monotone'
              }]
            },
        
            // Configuration options go here
            options: {
              maintainAspectRatio: false,
              title: {
                display: true,
                text: 'Sensor Data'
              },
              legend: {
                display: false
              },
              scales: {
                xAxes: [{
                  id:"x-axis",
                  type:"time",
                  time: {
                    unit: 'minute',
                    stepSize: 30
                  },
                  ticks: {
                    minRotation:0,
                    maxRotation:0
                  }
                }],
                yAxes: [{
                  ticks: {
                    beginAtZero:false
                  }
                }]
              },
              tooltips: {
                intersect: false
              },
              animation: {
                duration: 0
              },
              hover: {
                animationDuration: 0
              },
              
              // Zoom plugin options
              plugins: {
                zoom: {
                  pan: {
                    enabled: true,
                    mode: 'y',
                  },
                  zoom: {
                    enabled: true,
                    mode: 'y',
                  }
                }
              },
              
              onClick: function() {this.resetZoom()}
            }
        
        })
        this.plotData(this.chartData);
    }
});
