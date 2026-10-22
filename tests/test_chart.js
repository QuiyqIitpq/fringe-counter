const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const source=fs.readFileSync(path.join(__dirname,'../ui.js'),'utf8');
const code=source.slice(source.indexOf('function rangeIndices()'),source.indexOf('function drawChart()'));
let conditional=true;
const context={config:{sign:1,start:0,end:3,visible:[],cleaning:false,show_mean:false,smooth_display:false},report:{time:[0,1,2,3],rois:[],track:{delta:[0,1,null,2],valid:[true,true,false,true],estimated:[]}},$:()=>({checked:conditional})};
vm.createContext(context);vm.runInContext(code,context);
assert.equal(vm.runInContext('chartSeries().at(-1).points.at(-1)[1]',context),3,'Conditional graph must equal finite-increment sum across gaps');
conditional=false;assert.equal(vm.runInContext('chartSeries().at(-1).points.at(-1)[1]',context),0,'Unconnected measured segments must start at local zero');
console.log('2 chart regression checks passed');
