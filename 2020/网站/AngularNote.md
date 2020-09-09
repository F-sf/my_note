# Angular2

js写的前端框架

## 1. 安装

1. 安装nodejs **一个让js脱离浏览器运行的运行环境(解释器？)**

2. 安装npm和cnpm **js库管理工具，方便安装各种依赖库**

3. 安装angular：`cnpm install -g @angular/cli`

   `ng v`查看版本

## 2. 创建项目

* 创建：`ng new ProjName [--skip-install]`
* 安装依赖：`cd ProjName`、`cnpm install`
* 打开：`ng serve --open`

## 3. 文件目录结构

* `e2e`端对端测试用
* `node_modules`依赖安装位置
* `src`主要工作目录
  * `app`组件和根模块
    * `app.component.html/css/ts`根组件
    * `app.module.ts`Angular根模块 
  * `assets`静态资源文件
  * `environments`环境相关文件
  * `browserslist`支持浏览器配置
  * `favicon.ico`网页图标
  * `index.html`html入口文件(运行起点)
  * `main.ts`项目入口文件
  * `polyfills.ts`填充库
  * `styles.css`公共样式
  * `test.ts`测试入口文件
* `package.json`项目的配置文件
* `tsconfig.json`TypeScript配置文件

## 4. 常用操作

### 4.1 创建组件

* 创建组件component:

  `ng g component componentPath`

  在项目根目录下执行此命令，会在给出路径下创建新的组件文件夹。

### 4.2 动态绑定数据

* 文本节点绑定属性，用{{属性名}}：`<div>{{foo}}</div>`
* 标签内属性动态绑定数据，用[]：`<div [title]="foo"></div>`
* 解析ts中的html字符串，在html中给标签加属性：`<div [innerHTML]='foo'></div>`

### 4.3 ng中的循环

``` html
<!-- .ts -->
public foos:number[] = [11, 22, 33];

<!-- .html -->
// 遍历
<ul>
    <li *ngFor="let foo of foos">
        {{foo}}
	</li>
</ul>
// 索引
<ul>
    <li *ngFor="let foo of foos;let i=index;">
        {{i}}---{{foo}}
    </li>
</ul>
```

### 4.4 ng中的判断

``` html
<!-- .ts -->
public flag:boolean = true;

<!-- .html flag为false时，div标签不会被渲染-->
<div *ngIf="flag">Something</div>
<!-- 并没有ngElse -->
<div *ngIf="!flag">OtherThings</div>
```

### 4.5 ng中的SwitchCase

``` html
<span [ngSwitch]="foo">
	<p *ngSwitchCase="1">
        Do Something
    </p>
    <p *ngSwitchCase="2">
        Do Something
    </p>    
    <p *ngSwitchDefault>
        Do Something
    </p>    
</span>
```

### 4.6 ngClass和ngStyle

```php+HTML
<!-- .ts -->
public flag:boolean = true;
public attr:string = "red";
<!-- .html -->
<div [ngClass]="{'red':flag,'blue':flag}">
	<!-- 此处的flag可为各种表达式，如循环中的i==0 -->
    flag决定该元素的class属性
</div>

<div [ngStyle]="{'color':attr}">
  	attr可为各种表达式，决定该元素样式
</div>
```

### 4.7 管道pipe

``` html
<!-- .ts -->
today = new Date();
<!-- .html -->
<!-- date为ng自带管道函数，处理并格式化Date，也可自建其他函数 -->
{{today | date:'yyyy-MM-dd HH:mm:ss'}}
```

### 4.8 事件绑定

```html
<input type="text" (keyup)="keyUpFunc($event)" />  // keyup为要绑定的事件
```

``` typescript
// 目标组件class中添加方法：
public keyUpFunc(e){
    // e为获取到的事件对象
    console.log(e);
    // e.target拿取事件对象对应的DOM对象
    console.log(e.target)
}
```

### 4.9 数据和视图双向绑定

``` typescript
// 使用双向绑定需要在module.ts中引入FormsModule
import { FormsModule } from '@angular/forms';
@NgModule({
	// ...
  	imports: [
	  	// ...
      	FormsModule
  	],
  	// ...
})
// 在目标组件类中添加属性
data:string = "TestData";
```

```3html
// []表示绑定属性，()表示绑定事件
<input type="text" [(ngModule)]='data' />  // keywords为进行双向绑定的表达式
```

### 4.10 服务

> `服务`可用于工具类，或用于整个模块**共享数据**的类。

#### 4.10.1 创建

`ng g service servicePath`

还需要手动在module.ts中import服务，并在NgModule入口参数中的provider中添加。

#### 4.10.2 使用

​	在哪个组件用就在哪里import，然后以`public foo:fooService`的形式加入该组件的构造函数入口参数。在组件类中用`this.foo`调用该类。

### 4.11 获取DOM对象

#### 4.11.1 原生JS

​	一般在组件类的`ngAfterViewInit()`钩子函数中以原生JS的方式拿取DOM对象。该生命周期过后才可真正获取DOM对象。

#### 4.11.2 ViewChild

> 用于获取**子组件**内的属性或方法

```typescript
// html
// <app-myComponent #myComp></app-component>

export class MyComponent implements OnInit {
	@ViewChild('myComp') foo:any;    // ts 在组件类中添加装饰属性
    
    this.foo.myFunc();	// 调用子组件中方法
}
```

### 4.12 父子组件传值

```typescript
// 父->子
// 1. 父组件中定义属性、方法、也可传父组件对象本身
public foo:string = "123";
func(){}
// 2. 调用子组件时，在html中添加自定义属性，可传属性、方法、父组件本身
// <child [foo]="foo" [func]="func" [fatherObj]="this"></child>
// 3. 子组件使用Input装饰器装饰类属性接收值
import {Input} from '@angular/core';
class Child {
    @Input() foo:string;
    @Input() func:any;
    @Input() fatherObj:any;
    console.log(this.foo,this.func,this.fatherObj);
}

// 子->父 见4.11.2
// 也可用Output和EventEmitter使子组件的事件发生时通知父组件，详细可见官方手册angular.cn
```

### 4.13 Rxjs

> 用于异步操作，发布订阅模型，好像水很深。

### 4.14 http请求操作

```typescript
// 1. 在根模块中注入
import { HttpClientModule } from '@angular/common/http';
@NgModule({
    imports:[
        HttpClientModule,
    ]
})
// 2. 在要用的模块中引入
import { HttpClient,HttpHeaders } from '@angular/common/http';
class Component{
    constructor(public http:HttpClient){}
	let url="abc.com/index/aaa/bbb";
	// 此处为get操作
	this.http.get(url).subscribe((response)=>{
        // subscribe为Rxjs接收异步返回数据的操作，HttpModule内部使用Rxjs实现
        console.log(response);
    })
	// 此处为post操作
	const httpOptions = {headers: new HttpHeaders({'Content-Type': 'application/json'})};
	this.http.post(url,{'key':value, 'key2':value2},httpOptions).subscribe((response)=>{
        console.log(response);
    })
}
```

### 4.15 路由

> 可创建一个router-outlet的组件，动态变化。创建项目时询问是否创建路由选Yes即可创建模板。

#### 4.15.1 一般传值方式(get传值)

```typescript
// routing.module.ts
import { FooComponent } from './components/foo/foo.component';
const routes: Routes = [
  {path:"foo", component:FooComponent},	// 添加新路由
  {path:"**",redirectTo:"foo"}	 // 默认路由转至foo(path名)
];

// foo.component.ts
import { ActivateRoute } from '@angular/router';	// 路由传值时需引入
class FooComponent{
    constructor(public route:ActivateRoute){}
    this.route.queryParams.subscribe((data)=>{
        // subscribe为Rxjs接收异步返回数据的操作，路由传值内部也使用Rxjs实现
        console.log(data);
    })	
}
```

```html
<a routerLink="/foo" [queryParams]="{para1:1}">	// 第一个属性用于跳转，第二个用于路由传值
```

#### 4.15.2 动态路由传值方式(没明白有啥好处)

```typescript
// routing.module.ts
const routes: Routes = [
  {path:"foo/:id", component:FooComponent},	// 添加新路由
];

// foo.component.ts
import { ActivateRoute } from '@angular/router';	// 路由传值时需引入
class FooComponent{
    constructor(public route:ActivateRoute){}
    this.route.params.subscribe((data)=>{
        // subscribe为Rxjs接收异步返回数据的操作，路由传值内部也使用Rxjs实现
        console.log(data);
    })	
}
```

```html
<a [routerLink]="['/foo', 1]"></a>
```

#### 4.15.3 在JS中进行路由跳转

``` typescript
// 一般传值(get传值)时
// get传值JS跳转需引入，注意是Router，不是Route；另外可不用NavigationExtras
import { Router, NavigationExtras } from '@angular/router';	
class FooComponent{
    constructor(public router:Router){}
    let navigationExtras:NavigationExtras = {
        queryParams: {'para1':1}	// 跳转参数
    };
	this.router.navigate(['/foo'], navigatorExtras);  // 带参数跳转
	// 不用NavigationExtras时可这样写
	this.router.navigate(['/foo'], { queryParams: {'para1':1} });  
}
// 动态路由传值时
import { Router } from '@angular/router';	// 动态路由传值JS跳转需引入
class FooComponent{
    constructor(public router:Router){}
	this.router.navigate(['/foo', 1]);  // 若无参数，不加第二个数组项即可
}
```

#### 4.15.4 路由嵌套

```typescript
// html中在父组件内加入<route-outlet>元素
// ts中加入嵌套路由
const routes: Routes = [
  {
      path:"foo", component:FooComponent, children:[	// 子组件
          {path:"fooChild", component:FooChildComponent}
      ]
  },
];
```

### 4.16 自定义模块

> 可把一些组件和服务模块化，更易管理

#### 4.16.1 创建

* 在app目录下创建带路由的自定义模块：`ng g module module/myModule --routing`

* 为自定义模块创建根组件：`ng g component module/myModule`

* 为自定义模块创建组件or服务：`ng g component module/myModule/component/myComp`,

  ​														`ng g service module/myModule/service/myService`

* 自定义模块中的组件/服务/路由配置方式和根组件相同，外部调用时需引入该模块，若有模块内对象想被外部调用，需在`@Ngmodule({ export: [] })`中加入

#### 4.16.2 通过路由实现自定义模块懒加载

> 可以保证只在使用时加载子模块，减少加载时间

1. 在创建子模块时加入路由

2. 在子模块的路由.ts中加入

   ```javascript
   const routes: Routes = [
     {path:"", component:MyModuleComponent}
   ];
   ```

3. 在根模块的路由.ts中加入

   ```typescript
   const routes: Routes = [
     {
        path:"myModule",loadChildren:'./module/myModule/myModule.module#MyModuleModule'];
     },
   ];
   ```

   即可实现使用时模块懒加载

## 打包部署

> 调试和发布时代码上的区别只在自己写的配置文件中的服务器url

1. 更改服务器url为要配置的服务器ip
2. 执行ng build --prod命令打包项目
3. 将dist下生成的**文件夹内的文件**拷贝到SpringBoot工程src/main/resources/static目录下，注意index.html应直接在static下。

## 杂记

### css中的position

* 默认为static，此时完全走文档流，top、left、bottom等属性无效，仅可通过margin、border、padding布局。
* 常用为relative，相对于其在文档流中的原先位置进行定位，且会保留其本来在文档流中所占据的位置。
* absolute，相对于父级元素中上一个非static定位，会直接脱离文档流(意为可多元素重叠)。
* fixed，相对于浏览器原点定位，也会直接脱离文档流。

###  自定义样式设计思路

* 可通过一个父级div加入文本或图片进行完全放飞自我的设计，然后其实际对应的功能作为子元素加入，放到很大之后通过opacity和父级中加入overflow的方式使其做到外观和实际功能完全分离，且将功能的触发范围限制在外观之内。`这思路太有意思了...`

### ng-click和(click)

​	这两种风格分别是ng1和ng2的写法，ng1和ng2在使用和组织逻辑上可以说基本完全没有关系。网上很多博客仍保留前一种写法。使用ng2时设计思路完全组件化，模块化，比1更清晰、好复用、易上手。

### 强制类型转换

​	开发中遇到问题：对于某个input标签`document.getElementById("blog-file-input").files`会报错如下`Property 'files' does not exist on type 'HTMLElement'`。因为getElementById返回的默认类型为HTMLElement，需要用`(<HTMLInputElement> document.getElementById("blog-file-input")).files`进行类型转换才可跳过IDE的语法检查。

​	上述报错仅为IDE报错，浏览器中直接按第一种写法是可以运行的。-_-||

​	ts中的类型转换语法为<Type> a。

### Angular中使用JQuery

```shell
cnpm install jquery --save
npm install @types/jquery --save
# --save可将jquery和@types/jquery的依赖存入package.json
# 然后在需要使用jquery的ts文件中引入即可
# import * as $ from 'jquery';
```

> jquery和原生DOM虽然风格迥异，但其目的都是一样的。

### 文件下载问题

> 文件下载即可通过前端操作，也可通过后端操作。但一番折腾下来还是前端比较方便。

​    整体来说前端下载有用\<a>标签的download属性、和新建一个窗口然后window.open()两种方式。a标签应该是全面优于开新窗口。操作方式如下所示：

```js
const a = document.createElement('a');
a.setAttribute('download', '文件名,不需加后缀');
a.setAttribute('href', '要下载文件的URL');
a.click();
```

​    操作方式主要有两种思路，一是对于**已然确定的单个要下载的文件**，可以直接用上述代码定位到其URL。另一种是需要下载一系列文件，在后端打成压缩包后传输，这时我摸索的解决方法是在后端将压缩文件的二进制字节流直接写入http包的content，然后在前端设置好接收的类型为blob二进制字节流，然后将其转为URL再进行下载。

​	整个代码段如下：

```js
this.http.post(this.blogsURL+'downloadBlog', jsonObj, {responseType:'blob'}).subscribe(response=>{
    const blob = new Blob([response], { type: "application/zip" });
    const a = document.createElement('a');
    a.setAttribute('download', title);
    a.setAttribute('href', URL.createObjectURL(blob));
    a.click();
});
```

### Angular中接收http返回的坑

​	`this.http.get("url").subscribe(res=>{});`这种形式接收返回包时默认将content按json解析，若在使用Angular时遇到**Unexpected token in JSON at position 0**报错，很可能是此处引发的问题。

​	解决方法为手动设置返回类型如下：`this.http.get("url"，{responseType:'blob'}).subscribe(res=>{});`

​	其中responseType可设置为 json，arraybuffer，blob，text四种