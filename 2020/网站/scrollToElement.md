### JS简单实现滚动至某元素

> 开发中希望实现跳转到一个新页面并且自动滚动到某一位置的功能，网上很多方案都比较复杂或者不靠谱，在此记录一个简单的实现方法。

```html
<!-- html -->
<div id="my-container">
    <div id="my-element"/>    
</div>
```

```js
// js
let topOffset = document.getElementById("my-element").offsetTop;
document.getElementsById("my-container").scrollTo({top:topOffset, behavior:"smooth"});
// 如果是整个页面滚动的话，window.scrollTo()即可
```



