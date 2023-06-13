function getImageBrightness(theURL,callback) {
    var colorSum = 0;
    var img=new Image();
    img.onload=start;
    img.onerror=error;
    img.src=theURL;
    function start(){
        var canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        var ctx = canvas.getContext("2d");
        ctx.drawImage(img,0,0);
        var imageData = ctx.getImageData(0,0,canvas.width,canvas.height);
        var data = imageData.data;
        var r,g,b,avg;
            for(var x = 0, len = data.length; x < len; x+=4) {
            r = data[x];
            g = data[x+1];
            b = data[x+2];
            avg = Math.floor((r+g+b)/3);
            colorSum += avg;
        }
        var brightness = Math.floor(colorSum / (img.width*img.height));
        callback(brightness);
    }
    function error(){
        console.log('ERROR');
        img.src='/static/no-img.png';
    }
}

$(function () {
    $('img').each(function () {
        const src = $(this).attr('id');
        if (!src) return;
        let image = $(this);
        let txt = $('#txt_'+src.replace(".", "\\.")+ ' a');
        if(txt){
            getImageBrightness('/static/images/'+src,function(brightness) {
                //console.log(brightness, $('#txt_'+src.replace(".", "\\.")).text());
                image.attr('src','/static/images/'+src);
                if(brightness > 150){
                    txt.addClass('txtblack');
                }else{
                    txt.addClass('txtwhite');
                }
                txt.append(' ' + brightness)
            });        
        }
    });
});