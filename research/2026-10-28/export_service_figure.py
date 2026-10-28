"""Standalone scientific figure from saved exact finite-law results; no reruns."""
from hashlib import sha256
from pathlib import Path
import json
import reportlab
from reportlab.graphics.shapes import Drawing,String,Line,Circle,Group
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor,white,black
from reportlab.pdfgen import canvas

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/"output"/"pdf"


def main():
    iid_path=HERE/"service_rounds"/"round63.json"
    batch_path=HERE/"service_rounds"/"round67.json"
    iid=json.loads(iid_path.read_text(encoding="utf-8"))
    batch=json.loads(batch_path.read_text(encoding="utf-8"))
    data=[[(x["input"],x["maximum_service"]) for x in iid["rows"] if "maximum_service" in x]]
    for case in batch["cases"]:
        data.append([(x["input"],x["maximum_service"]) for x in case["rows"] if x["input"]>=1471])
    data.extend([[(1470,.75),(2100,.75)],[(1470,.8),(2100,.8)]])
    d=Drawing(760,480)
    d.add(String(32,450,"Complete-order service under a candidate final-station repair route",fontName="Helvetica-Bold",fontSize=14))
    d.add(String(32,430,"D=(750,150); normal-source class probabilities; eta=0.97; setup workload=0",fontName="Helvetica",fontSize=10,fillColor=HexColor("#444444")))
    plot=LinePlot()
    plot.x,plot.y,plot.width,plot.height=80,120,630,280
    plot.data=data
    plot.joinedLines=1
    plot.xValueAxis.valueMin=1470
    plot.xValueAxis.valueMax=2100
    plot.xValueAxis.valueSteps=[1500,1600,1700,1800,1900,2000,2100]
    plot.yValueAxis.valueMin=.5
    plot.yValueAxis.valueMax=.82
    plot.yValueAxis.valueSteps=[.5,.55,.6,.65,.7,.75,.8]
    plot.yValueAxis.labelTextFormat="%.2f"
    for axis in (plot.xValueAxis,plot.yValueAxis):
        axis.labels.fontName="Helvetica"
        axis.labels.fontSize=10
        axis.strokeColor=HexColor("#333333")
    plot.yValueAxis.visibleGrid=1
    plot.yValueAxis.gridStrokeColor=HexColor("#DDDDDD")
    plot.yValueAxis.gridStrokeWidth=.4
    colors=[HexColor("#0072B2"),HexColor("#D55E00"),HexColor("#009E73")]
    for i,color in enumerate(colors):
        plot.lines[i].strokeColor=color
        plot.lines[i].strokeWidth=1.8
    for i in (3,4):
        plot.lines[i].strokeColor=HexColor("#666666")
        plot.lines[i].strokeWidth=.8
        plot.lines[i].strokeDashArray=[5,4]
    d.add(plot)
    d.add(String(395,82,"Deterministic integer release I",fontName="Helvetica",fontSize=11,textAnchor="middle"))
    vertical=Group(String(0,0,"Joint full-order service probability",fontName="Helvetica",fontSize=11,textAnchor="middle"))
    vertical.transform=(0,1,-1,0,25,260)
    d.add(vertical)
    labels=["Maximum service: iid quality","Maximum service: kappa=1000","Maximum service: kappa=100"]
    for x,color,label in zip((70,290,515),colors,labels):
        d.add(Line(x,63,x+18,63,strokeColor=color,strokeWidth=2))
        d.add(String(x+24,59,label,fontName="Helvetica",fontSize=9.5))
    x=80+(1495-1470)/630*630
    y=120+(.7503494297908824-.5)/.32*280
    d.add(Circle(x,y,3,fillColor=black,strokeColor=white,strokeWidth=.6))
    d.add(String(70,42,"Black dot: selected iid setup policy, I=1495, service=0.75035 (F=2000). Dashed: 0.75 and 0.80 targets.",fontName="Helvetica",fontSize=9))
    d.add(String(70,26,"Hypothetical quality laws and repair route; fixed forward flow. Integer-grid segments guide the eye.",fontName="Helvetica",fontSize=9,fillColor=HexColor("#555555")))
    d.add(String(70,11,"Source: saved rounds63/67. Curves show service capability; setup fees affect profit, not the capability ceiling.",fontName="Helvetica",fontSize=8.5,fillColor=HexColor("#555555")))
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/"service_release_curve.pdf"
    pages=[d]
    sources=[Path(__file__),iid_path,batch_path]
    ce_path=HERE/"service_rounds"/"round76.json"
    if ce_path.exists():
        comparison=json.loads(ce_path.read_text(encoding="utf-8"))
        rows=comparison["rows"]
        over=max(rows,key=lambda x:x["matched_CE_minus_finite_batch"])
        under=min(rows,key=lambda x:x["matched_CE_minus_finite_batch"])
        chart=Drawing(760,480)
        chart.add(String(32,450,"Mean-quality plug-in estimates can overstate or understate service",fontName="Helvetica-Bold",fontSize=14))
        chart.add(String(32,430,"Matched output floor and integer returns; eta=0.97; S=0; maximal returns in every profile",fontName="Helvetica",fontSize=10,fillColor=HexColor("#444444")))
        axes=LinePlot()
        axes.x,axes.y,axes.width,axes.height=80,110,300,300
        axes.data=[[(.55,.55),(1.,1.)]]
        axes.joinedLines=1
        for axis in (axes.xValueAxis,axes.yValueAxis):
            axis.valueMin=.55
            axis.valueMax=1.
            axis.valueSteps=[.6,.7,.8,.9,1.]
            axis.labelTextFormat="%.1f"
            axis.labels.fontName="Helvetica"
            axis.labels.fontSize=10
        axes.yValueAxis.visibleGrid=1
        axes.yValueAxis.gridStrokeColor=HexColor("#DDDDDD")
        axes.yValueAxis.gridStrokeWidth=.4
        axes.lines[0].strokeColor=HexColor("#777777")
        axes.lines[0].strokeWidth=.8
        axes.lines[0].strokeDashArray=[4,3]
        chart.add(axes)
        px=lambda x:80+(x-.55)/.45*300
        py=lambda y:110+(y-.55)/.45*300
        for row in rows:
            chart.add(Circle(px(row["matched_floor_integer_return_mean_quality"]),py(row["random_initial_quality_random_success"]),2.6,fillColor=HexColor("#0072B2"),strokeColor=white,strokeWidth=.3))
        for row,color in ((over,HexColor("#D55E00")),(under,HexColor("#009E73"))):
            x=row["matched_floor_integer_return_mean_quality"]
            y=row["random_initial_quality_random_success"]
            chart.add(Line(px(x),py(x),px(x),py(y),strokeColor=color,strokeWidth=1.4))
            chart.add(Circle(px(x),py(y),4,fillColor=color,strokeColor=white,strokeWidth=.6))
        chart.add(String(230,72,"Mean-quality service probability",fontName="Helvetica",fontSize=11,textAnchor="middle"))
        vertical=Group(String(0,0,"Finite-batch service probability",fontName="Helvetica",fontSize=11,textAnchor="middle"))
        vertical.transform=(0,1,-1,0,25,260)
        chart.add(vertical)
        chart.add(String(420,390,"Largest overestimate in this subset",fontName="Helvetica-Bold",fontSize=12,fillColor=HexColor("#D55E00")))
        chart.add(String(420,371,f"D=650/250, I={over['input']:.4f}",fontName="Helvetica",fontSize=11))
        chart.add(String(420,352,f"Mean {100*over['matched_floor_integer_return_mean_quality']:.2f}% vs finite {100*over['random_initial_quality_random_success']:.2f}%",fontName="Helvetica",fontSize=11))
        chart.add(String(420,333,f"Difference: {100*over['matched_CE_minus_finite_batch']:+.2f} percentage points",fontName="Helvetica",fontSize=11))
        chart.add(String(420,290,"Largest underestimate in this subset",fontName="Helvetica-Bold",fontSize=12,fillColor=HexColor("#009E73")))
        chart.add(String(420,271,f"D=750/337, I={under['input']:.0f}",fontName="Helvetica",fontSize=11))
        chart.add(String(420,252,f"Mean {100*under['matched_floor_integer_return_mean_quality']:.2f}% vs finite {100*under['random_initial_quality_random_success']:.2f}%",fontName="Helvetica",fontSize=11))
        chart.add(String(420,233,f"Difference: {100*under['matched_CE_minus_finite_batch']:+.2f} percentage points",fontName="Helvetica",fontSize=11))
        for i,line in enumerate(("34 predefined inputs, 15 source demand pairs.","Dashed line: estimates agree.","Points below line: plug-in overestimates.","Same extended model and repair rule throughout.","Source's own fixed-fraction assumptions kept separate.")):
            chart.add(String(420,185-17*i,line,fontName="Helvetica",fontSize=9.5,fillColor=HexColor("#555555")))
        chart.add(String(70,38,"Exact finite-law model comparison; no Monte Carlo error bars. Always return, not economic startup policies.",fontName="Helvetica",fontSize=9))
        chart.add(String(70,20,"Source: saved round76. Inputs fixed by mean formula, first maximum-service integer, and economic input anchors.",fontName="Helvetica",fontSize=8.8,fillColor=HexColor("#555555")))
        pages.append(chart)
        sources.append(ce_path)
    grid_path=HERE/"service_rounds"/"round79.json"
    if grid_path.exists():
        grid=json.loads(grid_path.read_text(encoding="utf-8"))
        boundary=Drawing(760,480)
        boundary.add(String(32,450,"A mean-quality threshold can hide finite-batch service uncertainty",fontName="Helvetica-Bold",fontSize=14))
        boundary.add(String(32,430,"Same output floor and integer return rule; mean counts/successes vs random counts/successes",fontName="Helvetica",fontSize=10,fillColor=HexColor("#444444")))
        for left,demand,lower,upper,ticks in ((65,(500,300),1120,1200,[1120,1140,1160,1180,1200]),
                                             (425,(650,250),1270,1340,[1270,1290,1310,1330])):
            case=next(x for x in grid["cases"] if tuple(x["demands"])==demand)
            points=[x for x in case["points"] if lower<=x["input"]<=upper]
            panel=LinePlot()
            panel.x,panel.y,panel.width,panel.height=left,160,280,235
            panel.data=[[(x["input"],x["matched_CE"]) for x in points],
                        [(x["input"],x["finite_batch"]) for x in points],[(lower,.8),(upper,.8)]]
            panel.joinedLines=1
            panel.xValueAxis.valueMin=lower
            panel.xValueAxis.valueMax=upper
            panel.xValueAxis.valueSteps=ticks
            panel.yValueAxis.valueMin=0
            panel.yValueAxis.valueMax=1
            panel.yValueAxis.valueSteps=[0,.2,.4,.6,.8,1]
            panel.yValueAxis.labelTextFormat="%.1f"
            for axis in (panel.xValueAxis,panel.yValueAxis):
                axis.labels.fontName="Helvetica"
                axis.labels.fontSize=9
            panel.yValueAxis.visibleGrid=1
            panel.yValueAxis.gridStrokeColor=HexColor("#DDDDDD")
            panel.yValueAxis.gridStrokeWidth=.4
            for j,color in enumerate((HexColor("#D55E00"),HexColor("#0072B2"),HexColor("#777777"))):
                panel.lines[j].strokeColor=color
                panel.lines[j].strokeWidth=1.7 if j<2 else .7
            panel.lines[2].strokeDashArray=[4,3]
            boundary.add(panel)
            boundary.add(String(left+140,407,f"D={demand[0]}/{demand[1]}",fontName="Helvetica-Bold",fontSize=11,textAnchor="middle"))
            boundary.add(String(left+140,125,"Integer release I",fontName="Helvetica",fontSize=10,textAnchor="middle"))
        vertical=Group(String(0,0,"Joint full-order service probability",fontName="Helvetica",fontSize=10,textAnchor="middle"))
        vertical.transform=(0,1,-1,0,20,278)
        boundary.add(vertical)
        for x,color,label in ((65,"#D55E00","Mean quality / successes"),(295,"#0072B2","Random quality / successes"),(535,"#777777","0.80 reference")):
            boundary.add(Line(x,102,x+20,102,strokeColor=HexColor(color),strokeWidth=1.8))
            boundary.add(String(x+26,98,label,fontName="Helvetica",fontSize=10))
        boundary.add(String(65,74,"D=500/300, I=1152: mean 0.96559 vs finite 0.50967 (+45.59 percentage points).",fontName="Helvetica",fontSize=10))
        boundary.add(String(65,56,"D=650/250, I=1297: mean 0 vs finite 0.48917 (-48.92 percentage points).",fontName="Helvetica",fontSize=10))
        boundary.add(String(65,34,"Source: round79 full grid (15 orders x 2101 inputs); 151 false >=0.80 claims. Lines guide integer points only.",fontName="Helvetica",fontSize=8.8))
        boundary.add(String(65,17,"Hypothetical extended model; no factory validation and no claim that the original fixed-fraction model is erroneous.",fontName="Helvetica",fontSize=8.8,fillColor=HexColor("#555555")))
        pages.append(boundary)
        sources.append(grid_path)
    document=canvas.Canvas(str(path),pagesize=(760,480))
    for page in pages:
        renderPDF.draw(page,document,0,0)
        document.showPage()
    document.save()
    manifest={"reportlab_version":reportlab.Version,"output":str(path.relative_to(ROOT)),"pages":len(pages),
              "source_sha256":{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sources},
              "scope":"Plot of exact finite-law integer-grid values; no empirical factory claim or continuous-input optimum."}
    (HERE/"service_figure_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(path)


if __name__=="__main__":
    main()
