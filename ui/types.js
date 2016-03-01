var types = (function() {
"use strict";

//// Configuration

var config = {
    statcodes: ['type-word', 'type-token', 'hapax-word', 'hapax-token', 'token-word'],
    basecolor: '#337ab7',
    axisoffset: 10,
    leftaxisextra: 4,
    bottomaxisextra: 2,
    triangle_threshold: 0.1,
    p_threshold: 0.1,
    fdr_threshold: 0.1,
    large_area: 400,
    small_area: 120,
    label_corner_radius: 4,
    label_x_offset: 16,
    label_y_offset: 5,
    label_x_margin: 2,
    bar_width: 50,
    sbar_width: 25,
    max_aspect: 1.75,
    min_aspect: 1.0
};

//// Auxiliary functions

var get1 = function(a, k1) {
    return (a && k1) ? a[k1] : null;
};

var get2 = function(a, k1, k2) {
    return get1(get1(a, k1), k2);
};

var get3 = function(a, k1, k2, k3) {
    return get1(get2(a, k1, k2), k3);
};

var get4 = function(a, k1, k2, k3, k4) {
    return get1(get3(a, k1, k2, k3), k4);
};

var get0list = function(a) {
    return a ? a : [];
};

var get0obj = function(a) {
    return a ? a : {};
};

var get0first = function(a) {
    return (a && a.length) ? a[0] : null;
};

var get0num = function(a) {
    return a ? +a : 0;
};

var get1list = function(a, k1) {
    return get0list(get1(a, k1));
};

var get2list = function(a, k1, k2) {
    return get0list(get2(a, k1, k2));
};

var get3list = function(a, k1, k2, k3) {
    return get0list(get3(a, k1, k2, k3));
};

var get1first = function(a, k1) {
    return get0first(get1(a, k1));
};

var get1num = function(a, k1) {
    return get0num(get1(a, k1));
};

var get1obj = function(a, k1) {
    return get0obj(get1(a, k1));
};

var get2obj = function(a, k1, k2) {
    return get0obj(get2(a, k1, k2));
};

var set3 = function(a, k1, k2, k3, v) {
    if (!a[k1]) {
        a[k1] = {};
    }
    if (!a[k1][k2]) {
        a[k1][k2] = {};
    }
    a[k1][k2][k3] = v;
};

var add1 = function(a, k, v) {
    if (!a[k]) {
        a[k] = v;
    } else {
        a[k] += v;
    }
};

var push1 = function(a, k, v) {
    if (!a[k]) {
        a[k] = [v];
    } else {
        a[k].push(v);
    }
};

var sort_numbers = function(a) {
    a.sort(function(a, b) { return a-b; });
};

var translate = function(x, y) {
    return "translate("+x+","+y+")";
};

var set_translate = function(e, x, y) {
    return e.attr("transform", translate(x, y));
};

var opt_decode = function(x) {
    if (!x || x === "n") {
        return null;
    } else {
        return x.substring(1);
    }
};

var opt_encode = function(x) {
    if (!x) {
        return "n";
    } else {
        return "p" + x;
    }
};

var hash_decode = function(x) {
    if (!x) {
        return null;
    } else {
        return decodeURIComponent(x);
    }
};

var hash_encode = function(x) {
    if (!x) {
        return "";
    } else {
        return encodeURIComponent(x);
    }
};

var compactify = function(t) {
    var compact = [];
    var cur = null;
    for (var i = 0; i < t.length; ++i) {
        var x = t[i];
        if (!Array.isArray(x)) {
            x = ["span", x];
        }
        if (!cur) {
            cur = x;
        } else if (cur[0] === x[0]) {
            cur[1] += x[1];
        } else {
            compact.push(cur);
            cur = x;
        }
    }
    if (cur) {
        compact.push(cur);
    }
    return compact;
};

var textmaker = function(e, t) {
    var compact = compactify(t);
    for (var i = 0; i < compact.length; ++i) {
        var x = compact[i];
        e.append(x[0]).text(x[1]);
    }
};

var calc_score = function(a, b) {
    return [
        (a+0) / (b+2),
        (a+1) / (b+2),
        (a+2) / (b+2)
    ];
};

var f_large = d3.format("n");
var f_fraction = d3.format(".2r");
var f_fraction3 = d3.format(".3f");

var f_empty = function(f, x) {
    if (x === null || x === undefined) {
        return '';
    } else {
        return f(x);
    }
};

//// View: Plot

/*
    svg#plot
        g#curveareag                (translated)
            g#bg
            rect#cliprect
            g#clippedg              (clipped)
                g#curveg            (zoom -> translated & scaled)
                    path ...
            g#textbgareag[0]
                rect ...
            g#textbgareag[1]
                rect ...
            g#pointareag
                path ...
            g#textareag
                text ...
        g#xaxisg                    (translated)
        g#yaxisg                    (translated)
*/

var Plot = function(view) {
    this.ctrl = view.ctrl;
    this.plotdiv = view.content1.append("div").attr("class", "plot");
    this.plot = this.plotdiv.append("svg");
    this.curveareag = this.plot.append("g");
    this.bg = this.curveareag.append("rect").attr("class", "bg");
    this.cliprect = this.curveareag.append("clipPath")
        .attr("id", "plotclip").append("rect").attr("class", "bg");
    this.clippedg = this.curveareag.append("g")
        .attr("clip-path", "url(#plotclip)");
    this.textbgareag = [];
    for (var i = 0; i < 2; ++i) {
        this.textbgareag.push(this.curveareag.append("g"));
    }
    this.pointareag = this.curveareag.append("g");
    this.textareag = this.curveareag.append("g");
    this.curveg = this.clippedg.append("g");
    this.xaxisg = this.plot.append("g").attr("class", "x axis");
    this.yaxisg = this.plot.append("g").attr("class", "y axis");
    this.xscale = d3.scale.linear();
    this.yscale = d3.scale.linear();
    this.xaxis = d3.svg.axis().scale(this.xscale).orient("bottom");
    this.yaxis = d3.svg.axis().scale(this.yscale).orient("left");
    this.zoom = d3.behavior.zoom().scaleExtent([1,10]);
    this.curveareag.call(this.zoom);
    this.marginbase = 0;
    this.xticks = 0;
    this.yticks = 0;
    this.zoom.on('zoom', this.ev_zoom.bind(this));

    this.ctrldiv = view.content2.append("div").attr("class", "plotcontrol");
    view.info = view.content2.append("div").attr("class", "info");

    var on_settings = {
        'change': this.ev_settings_changed.bind(this),
        'input': this.ev_settings_changed.bind(this)
    };
    var label;
    label = this.ctrldiv.append("label").text("X ticks:");
    this.settings_yticks = label.append("input")
        .attr("type", "range")
        .attr("min", "0")
        .attr("max", "10")
        .attr("value", "5")
        .on(on_settings);
    label = this.ctrldiv.append("label").text("Y ticks:");
    this.settings_xticks = label.append("input")
        .attr("type", "range")
        .attr("min", "0")
        .attr("max", "10")
        .attr("value", "5")
        .on(on_settings);
    label = this.ctrldiv.append("label").text("Margins:");
    this.settings_margin = label.append("input")
        .attr("type", "range")
        .attr("min", "0")
        .attr("max", "40")
        .attr("value", "20")
        .on(on_settings);
    this.settings_reset = this.ctrldiv.append("button")
        .attr("type", "button")
        .attr("disabled", "disabled")
        .text("Reset")
        .on('click', this.ev_settings_reset.bind(this));
    this.refresh_settings();
};

Plot.prototype.setaxis = function() {
    this.xaxisg.call(this.xaxis);
    this.yaxisg.call(this.yaxis);
};

Plot.prototype.setscale = function() {
    this.zoom.translate([0,0]).scale(1);
    this.curveg.attr("transform", null);
    this.xscale.domain([0, this.curves.maxx]);
    this.yscale.domain([0, this.curves.maxy]);
    this.zoom.x(this.xscale).y(this.yscale);
    this.setaxis();
};

Plot.prototype.recalc_axes = function() {
    var margin = {
        left: this.marginbase,
        right: this.marginbase,
        top: this.marginbase,
        bottom: this.marginbase
    };
    if (this.xticks) {
        margin.bottom *= config.bottomaxisextra;
    }
    if (this.yticks) {
        margin.left *= config.leftaxisextra;
    }
    var fullwidth = parseInt(this.plotdiv.style('width'), 10);
    var fullheight = parseInt(this.plotdiv.style('height'), 10);
    if (fullwidth > config.max_aspect * fullheight) {
        fullwidth = Math.floor(config.max_aspect * fullheight);
    } else if (fullwidth < config.min_aspect * fullheight) {
        fullheight = Math.floor(fullwidth / config.min_aspect);
    }

    var plotwidth = fullwidth - margin.left - margin.right;
    var plotheight = fullheight - margin.top - margin.bottom;
    this.plot.style('width', fullwidth + 'px');
    this.plot.style('height', fullheight + 'px');
    this.bg.attr('width', plotwidth);
    this.bg.attr('height', plotheight);
    this.cliprect.attr('x', -1);
    this.cliprect.attr('y', -1);
    this.cliprect.attr('width', plotwidth+2);
    this.cliprect.attr('height', plotheight+2);
    this.xaxis.ticks(this.xticks);
    this.yaxis.ticks(this.yticks);
    this.xaxisg.style("visibility", this.xticks ? "visible" : "hidden");
    this.yaxisg.style("visibility", this.yticks ? "visible" : "hidden");
    this.xscale.range([0, plotwidth]);
    this.yscale.range([plotheight, 0]);
    set_translate(this.xaxisg, margin.left, plotheight + margin.top + config.axisoffset);
    set_translate(this.yaxisg, margin.left - config.axisoffset, margin.top);
    set_translate(this.curveareag, margin.left, margin.top);
    this.setscale();
};

Plot.prototype.recalc_curves = function() {
    var plot = this;
    var base = d3.hsl(config.basecolor);
    var f = 0.7;
    var mid = 2;
    this.paths
        .style("fill", function(d, i) {
            if (i < mid) {
                return base.brighter(f*(mid-i));
            } else {
                return base.darker(f*(i-mid));
            }
        })
        .attr("d", function(curve) {
            var gen = d3.svg.area()
                .x(function(d) { return plot.xscale(d.x); })
                .y0(function(d) { return plot.yscale(d.y0); })
                .y1(function(d) { return plot.yscale(d.y1); });
            return gen(curve.data);
        });
};

Plot.prototype.within_bounds = function(xx, yy) {
    var x = this.xscale(xx);
    var y = this.yscale(yy);
    var x0 = this.xscale.range()[0];
    var x1 = this.xscale.range()[1];
    var y0 = this.yscale.range()[1];
    var y1 = this.yscale.range()[0];
    return x0 <= x && x <= x1 && y0 <= y && y <= y1;
};

Plot.prototype.recalc_points = function() {
    var x0 = this.xscale.range()[0];
    var x1 = this.xscale.range()[1];
    var y0 = this.yscale.range()[1];
    var y1 = this.yscale.range()[0];
    var plot = this;
    var coord = function(d) {
        var x = plot.xscale(d.x);
        var y = plot.yscale(d.y);
        var bounds = (x0 <= x && x <= x1 && y0 <= y && y <= y1);
        var vis = bounds ? "visible" : "hidden";
        return {x: x, y: y, vis: vis};
    };

    var pointset = function(d) {
        var c = coord(d);
        d3.select(this)
            .attr("transform", translate(c.x, c.y))
            .attr("d", d3.svg.symbol().size(d.area).type(d.sym))
            .style("visibility", c.vis);
    };
    var labelset = function(d) {
        var c = coord(d);
        d3.select(this)
            .attr("x", c.x + config.label_x_offset)
            .attr("y", c.y + config.label_y_offset)
            .text(d.collectioncode)
            .style("visibility", c.vis);
    };
    var bgset = function(d,i) {
        var c = coord(d);
        var bbox = plot.texts[0][i].getBBox();
        d3.select(this)
            .attr("x", bbox.x - config.label_x_margin)
            .attr("y", bbox.y)
            .attr("width", bbox.width + 2 * config.label_x_margin)
            .attr("height", bbox.height)
            .style("visibility", c.vis);
    };

    this.marks.each(pointset);
    this.texts.each(labelset);
    for (var j = 0; j < 2; ++j) {
        this.textbgs[j].each(bgset);
    }
};

Plot.prototype.recalc_plot = function() {
    this.recalc_axes();
    this.recalc_curves();
    this.recalc_points();
};

Plot.prototype.set_curves = function(curves) {
    // needs recalc
    this.curves = curves;
    this.paths = this.curveg.selectAll("path").data(this.curves.data);
    this.paths.exit().remove();
    this.paths.enter().append("path")
        .attr("class", "curve")
        .attr("vector-effect", "non-scaling-stroke");
};

Plot.prototype.set_points = function(points) {
    // needs recalc
    for (var i = 0; i < points.length; ++i) {
        var d = points[i];
        if (d.above < config.triangle_threshold) {
            d.sym = "triangle-up";
        } else if (d.below < config.triangle_threshold) {
            d.sym = "triangle-down";
        } else {
            d.sym = "square";
        }
        d.area = (d.sel ? config.large_area : config.small_area);
    }
    var ctrl = this.ctrl;
    this.points = points;
    this.marks = this.pointareag.selectAll("path").data(this.points);
    this.marks.exit().remove();
    this.marks.enter().append("path")
        .attr("class", "point")
        .on("click", ctrl.ev_point_click.bind(ctrl));
    this.texts = this.textareag.selectAll("text").data(this.points);
    this.texts.exit().remove();
    this.texts.enter().append("text")
        .attr("class", "pointlabel")
        .on("click", ctrl.ev_point_click.bind(ctrl));
    this.textbgs = [null, null];
    for (var j = 0; j < 2; ++j) {
        this.textbgs[j] = this.textbgareag[j].selectAll("rect").data(this.points);
        this.textbgs[j].exit().remove();
        this.textbgs[j].enter().append("rect")
            .attr("class", j ? "pointlabelbg2" : "pointlabelbg1")
            .attr("rx", config.label_corner_radius)
            .attr("ry", config.label_corner_radius)
            .on("click", ctrl.ev_point_click.bind(ctrl));
    }
};

Plot.prototype.ev_zoom = function() {
    this.curveg.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
    this.setaxis();
    this.recalc_points();
    this.settings_reset.attr('disabled', null);
};

Plot.prototype.reset_all = function() {
    var inputs = [this.settings_xticks, this.settings_yticks, this.settings_margin];
    for (var i = 0; i < inputs.length; ++i) {
        inputs[i].property("value", inputs[i].attr("value"));
    }
    this.settings_reset.attr('disabled', 'disabled');
};

Plot.prototype.refresh_settings = function() {
    this.marginbase = +this.settings_margin.property("value");
    this.xticks = +this.settings_xticks.property("value");
    this.yticks = +this.settings_yticks.property("value");
};

Plot.prototype.ev_settings_reset = function() {
    this.reset_all();
    this.refresh_settings();
    this.recalc_plot();
};

Plot.prototype.ev_settings_changed = function() {
    this.refresh_settings();
    this.recalc_plot();
    this.settings_reset.attr('disabled', null);
};

//// Tables

var stop_propagation = function(e) {
    e.stopPropagation();
};

var td_builder = function(d) {
    var kind = d.column.kind;
    var val = kind === 'pad' ? null : d.column.val(d.row);
    var e;
    var w;
    if (val === null || val === undefined) {
        e = document.createTextNode('');
    } else if (kind === 'link') {
        if (val.link) {
            e = document.createElement('a');
            e.appendChild(document.createTextNode(val.label));
            e.setAttribute('href', val.link);
            e.setAttribute('target', '_blank');
            e.onclick = stop_propagation;
        } else {
            e = document.createTextNode(val.label);
        }
    } else if (kind === 'wrap') {
        e = document.createElement('span');
        e.appendChild(document.createTextNode(val));
    } else if (kind === 'score') {
        e = document.createElement('span');
        w = [];
        w.push(Math.round(config.bar_width * val[0]));
        w.push(Math.round(config.bar_width * (val[2] - val[0])));
        w.push(config.bar_width - w[0] - w[1]);
        if (w[2] < 0) {
            w[1] += w[2];
            w[2] = 0;
        }
        for (var i = 0; i < 3; ++i) {
            var ee = document.createElement('span');
            ee.setAttribute('class', 'bar' + i);
            ee.setAttribute('style', 'border-left-width: ' + w[i] + 'px');
            e.appendChild(ee);
        }
    } else if (kind === 'num') {
        e = document.createElement('span');
        var e1 = document.createElement('span');
        var e2 = document.createElement('span');
        e1.appendChild(document.createTextNode(d.column.format(val)));
        var x = val / (d.max ? d.max : 1);
        w = [];
        w.push(Math.round(config.sbar_width * x));
        w.push(config.sbar_width - w[0]);
        e2.setAttribute('class', 'bar0 bar_pad');
        e2.setAttribute('style',
            'border-left-width: ' + w[0] + 'px' + ';' +
            'border-right-width: ' + w[1] + 'px'
        );
        e.appendChild(e1);
        e.appendChild(e2);
    } else {
        e = document.createTextNode(val);
    }
    return e;
};

var table_builder = function(columns, data, table, row_hook) {
    var get_max = function(c) {
        if (c.kind !== 'num') {
            return null;
        }
        return d3.max(data, function(v) { return c.val(v); });
    };
    var max = columns.map(get_max);
    table.selectAll("*").remove();
    var head = table.append("thead");
    var body = table.append("tbody");
    var tr = body.selectAll("tr")
        .data(data).enter()
        .append("tr");
    if (row_hook) {
        tr.classed("clickable", true);
    }
    var td = tr.selectAll("td")
        .data(function(row) {
            return columns.map(function(c,i) {
                return { row: row, column: c, max: max[i] };
            });
        }).enter().append("td");
    if (row_hook) {
        td.on("click", row_hook);
    }
    td.append(td_builder);
    td.attr("class", function(d) { return d.column.classed; });
    td.classed("right", function(d) { return d.column.right; });
    var th;
    var sort_key = null;
    var th_style = function() {
        th.classed("active", function(c, i) {
            return c.key && (i === sort_key);
        });
        th.classed("inactive", function(c, i) {
            return c.key && (i !== sort_key);
        });
    }
    var sorter = function(c, i) {
        if (!c.key) {
            return;
        }
        tr.sort(function(a, b) {
            return d3.ascending(c.key(a), c.key(b));
        });
        sort_key = i;
        th_style();
    };
    th = head.append("tr").selectAll("th")
        .data(columns).enter()
        .append("th")
        .on("click", sorter);
    th_style();
    th.html(function(d) { return d.html; });
    th.classed("right", function(d) { return !d.hcenter && (d.right || d.hright); });
    th.classed("center", function(d) { return d.hcenter; });
    return tr;
};

var ResultTable = function(view) {
    this.ctrl = view.ctrl;
    this.table = view.content1.append("table").classed("results", true);
    view.info = view.content2.append("div").attr("class", "info");
};

var SampleTable = function(view) {
    this.ctrl = view.ctrl;
    this.table = view.content1.append("table").classed("samples", true);
};

var TypeTable = function(view) {
    this.ctrl = view.ctrl;
    this.table = view.content1.append("table").classed("types", true);
};

ResultTable.prototype.set_results = function(model) {
    var ctrl = this.ctrl;
    var db = model.db;
    this.table.selectAll("*").remove();

    var columns = [
        ['corpus', function(p) { return p.corpuscode; }],
        ['dataset', function(p) { return p.datasetcode; }],
        ['collection', function(p) { return p.collectioncode; }],
        ['axes', function(p) { return db.statcode_map[p.statcode].label; }],
        ['side', function(p) { return p.side; }],
        ['p-value', function(p) {
            return f_fraction(p.fraction);
        }],
        ['FDR', function(p) {
            if (p.fdr < 1) {
                return f_fraction(p.fdr);
            } else {
                return "> 1";
            }
        }]
    ];

    var head = this.table.append("thead");
    head.append("tr").selectAll("th")
        .data(columns).enter()
        .append("th").text(function(d) {
            return d[0];
        });
    var body = this.table.append("tbody");
    this.rows = body.selectAll("tr")
        .data(db.point_ordered).enter()
        .append("tr")
        .classed("clickable", true);
    this.rows.selectAll("td")
        .data(function(row) {
            return columns.map(function(c) {
                return { row: row, column: c };
            });
        }).enter()
        .append("td").text(function(d) {
            return d.column[1](d.row);
        })
        .on("click", ctrl.ev_result_cell_click.bind(ctrl));
};

SampleTable.prototype.set_samples = function(model) {
    var columns = [
        {
            html: 'sample',
            kind: 'link',
            val: function(p) { return { label: p.samplecode, link: p.link }; },
            key: function(p) { return p.samplecode; }
        },
        {
            html: 'description',
            kind: 'plain',
            val: function(p) { return p.description; },
            key: function(p) { return p.description; }
        },
        {
            html: model.db.data.label.word.labeltext,
            kind: 'num',
            format: f_large,
            hcenter: true,
            right: true,
            val: function(p) { return p.wordcount; },
            key: function(p) { return -p.wordcount; }
        },
        {
            html: model.db.data.label.token.labeltext,
            kind: 'num',
            format: f_large,
            hcenter: true,
            right: true,
            val: function(p) { return p.tokens; },
            key: function(p) { return -p.tokens; }
        },
        {
            html: "/1000",
            kind: 'num',
            format: f_fraction,
            hcenter: true,
            right: true,
            val: function(p) { return p.tokens/p.wordcount*1000; },
            key: function(p) { return -p.tokens/p.wordcount; }
        },
        {
            html: model.db.data.label.type.labeltext,
            kind: 'num',
            format: f_large,
            hcenter: true,
            right: true,
            val: function(p) { return p.types; },
            key: function(p) { return -p.types; }
        },
        {
            html: model.db.data.label.hapax.labeltext,
            kind: 'num',
            format: f_large,
            hcenter: true,
            right: true,
            val: function(p) { return p.hapaxes; },
            key: function(p) { return -p.hapaxes; }
        },
        { kind: 'pad' },
        {
            html: "unique",
            kind: 'plain',
            classed: 'wrap small',
            val: function(p) { return p.unique.join(" "); },
            key: function(p) { return -p.unique.length; }
        }
    ];

    this.rows = table_builder(
        columns,
        model.get_samples(),
        this.table,
        this.ctrl.ev_sample_cell_click.bind(this.ctrl)
    );
};

TypeTable.prototype.set_tokens = function(model) {
    var columns = [
        {
            html: 'type',
            kind: 'plain',
            val: function(p) { return p.shortlabel; },
            key: function(p) { return p.shortlabel; }
        },
        {
            html: model.db.data.label.token.labeltext,
            kind: 'num',
            format: f_large,
            right: true,
            hcenter: true,
            val: function(p) { return p.tokencount; },
            key: function(p) { return -p.tokencount; }
        },
        {
            html: 'in collection',
            kind: 'num',
            format: f_large,
            right: true,
            hcenter: true,
            val: function(p) { return p.tokencount_collection; },
            key: function(p) { return -p.tokencount_collection; }
        },
        {
            html: 'fraction',
            kind: 'num',
            format: f_fraction3,
            right: true,
            hcenter: true,
            val: function(p) { return p.tokencount_fraction; },
            key: function(p) { return -p.tokencount_fraction; }
        },
        {
            html: 'score',
            kind: 'score',
            hcenter: true,
            val: function(p) { return p.tokencount_score; },
            key: function(p) { return -p.tokencount_score[1]; }
        },
        {
            html: 'samples',
            kind: 'num',
            format: f_large,
            right: true,
            hcenter: true,
            val: function(p) { return p.samplecount; },
            key: function(p) { return -p.samplecount; }
        },
        {
            html: 'in collection',
            kind: 'num',
            format: f_large,
            right: true,
            hcenter: true,
            val: function(p) { return p.samplecount_collection; },
            key: function(p) { return -p.samplecount_collection; }
        },
        {
            html: 'fraction',
            kind: 'num',
            format: f_fraction3,
            right: true,
            hcenter: true,
            val: function(p) { return p.samplecount_fraction; },
            key: function(p) { return -p.samplecount_fraction; }
        },
        {
            html: 'score',
            kind: 'score',
            hcenter: true,
            val: function(p) { return p.samplecount_score; },
            key: function(p) { return -p.samplecount_score[1]; }
        }
    ];

    this.rows = table_builder(
        columns,
        model.get_tokens(),
        this.table,
        this.ctrl.ev_token_cell_click.bind(this.ctrl)
    );
};

ResultTable.prototype.set_sel = function(model) {
    if (this.rows) {
        this.rows.classed("selected", function(d) {
            return model.sel.corpuscode === d.corpuscode &&
                model.sel.datasetcode === d.datasetcode &&
                model.sel.collectioncode === d.collectioncode &&
                model.sel.statcode === d.statcode;
        });
    }
};

SampleTable.prototype.set_sel = function(model) {
    if (this.rows) {
        this.rows.classed("selected", function(d) {
            return model.sel.corpuscode === d.corpuscode &&
                model.sel.samplecode === d.samplecode;
        });
    }
};

TypeTable.prototype.set_sel = function(model) {
    if (this.rows) {
        this.rows.classed("selected", function(d) {
            return model.sel.corpuscode === d.corpuscode &&
                model.sel.datasetcode === d.datasetcode &&
                model.sel.tokencode === d.tokencode;
        });
    }
};

//// View

var View = function(ctrl) {
    this.ctrl = ctrl;
    this.content1 = d3.select("#content1");
    this.content2 = d3.select("#content2");
    this.window1 = d3.select("#window1");
    this.window2 = d3.select("#window2");
};

View.prototype.set_page = function(model) {
    this.content1.selectAll("*").remove();
    this.content2.selectAll("*").remove();
    this.info = null;
    var p_main    = !model.sel.pagecode;
    var p_samples = model.sel.pagecode === 'samples';
    var p_types   = model.sel.pagecode === 'types';
    var p_plot    = model.sel.pagecode === 'plot';
    this.results = p_main    ? new ResultTable(this) : null;
    this.samples = p_samples ? new SampleTable(this) : null;
    this.types   = p_types   ? new TypeTable(this)   : null;
    this.plot    = p_plot    ? new Plot(this)        : null;
    this.window1.node().focus();
};

View.prototype.set_curves = function(model) {
    if (this.plot) {
        this.plot.set_curves(model.get_curves());
        this.plot.recalc_axes();
        this.plot.recalc_curves();
    }
};

View.prototype.set_points = function(model) {
    if (this.plot) {
        this.plot.set_points(model.get_points());
        this.plot.recalc_points();
    }
};

View.prototype.set_sel = function(model) {
    if (this.results) {
        this.results.set_sel(model);
    }
    if (this.samples) {
        this.samples.set_sel(model);
    }
    if (this.types) {
        this.types.set_sel(model);
    }
};

View.prototype.set_results = function(model) {
    if (this.results) {
        this.results.set_results(model);
    }
};

View.prototype.set_samples = function(model) {
    if (this.samples) {
        this.samples.set_samples(model);
    }
};

View.prototype.set_tokens = function(model) {
    if (this.types) {
        this.types.set_tokens(model);
    }
};

View.prototype.set_context = function(model) {
/*
    var table = this.context_table;
    if (!table) {
        return;
    }

    var sample_data = model.db.sample_data[model.sel.corpuscode][model.sel.datasetcode];
    var columns = [
        {
            html: 'sample',
            kind: 'link',
            val: function(p) { return { label: p.samplecode, link: sample_data[p.samplecode].link }; },
            key: function(p) { return p.samplecode; }
        },
        {
            html: 'description',
            kind: 'plain',
            val: function(p) { return sample_data[p.samplecode].description; },
            key: function(p) { return sample_data[p.samplecode].description; }
        },
        {
            html: 'token',
            kind: 'plain',
            val: function(p) { return p.shortlabel; },
            key: function(p) { return p.shortlabel; }
        },
        { kind: 'pad' },
        {
            html: 'before',
            kind: 'wrap',
            classed: 'before',
            hright: true,
            val: function(p) { return p.before; },
            key: function(p) { return p.before_sort; }
        },
        { kind: 'pad' },
        {
            html: 'word',
            kind: 'link',
            classed: 'word',
            hcenter: true,
            val: function(p) { return { label: p.word, link: p.link }; },
            key: function(p) { return p.word_sort; }
        },
        { kind: 'pad' },
        {
            html: 'after',
            kind: 'wrapwrap',
            classed: 'after',
            val: function(p) { return p.after; },
            key: function(p) { return p.after_sort; }
        }
    ];

    this.context_rows = table_builder(
        columns, 
        model.get_context(),
        table
    );
*/
};

View.prototype.set_info = function(model) {
    if (!this.info) {
        return;
    }

    this.info.selectAll("*").remove();
    var stat = model.get_stat();
    var corpus = model.get_corpus();
    var dataset = model.get_dataset();
    var p = model.get_point();
    var t;

    if (corpus) {
        t = [];
        t.push("Corpus ");
        t.push(["strong", model.sel.corpuscode]);
        t.push(" contains ");
        t.push(f_large(corpus.samplecount) + " samples");
        t.push(" and ");
        t.push(f_large(corpus.wordcount) + " " + model.db.data.label.word.labeltext);
        t.push(".");
        textmaker(this.info.append("p"), t);
    }

    if (dataset) {
        t = [];
        t.push("Dataset ");
        t.push(["strong", model.sel.datasetcode]);
        t.push(" contains ");
        t.push(f_large(dataset.hapaxes) + " " + model.db.data.label.hapax.labeltext);
        t.push(", ");
        t.push(f_large(dataset.tokens) + " " + model.db.data.label.type.labeltext);
        t.push(", and ");
        t.push(f_large(dataset.types) + " " + model.db.data.label.token.labeltext);
        t.push(".");
        textmaker(this.info.append("p"), t);
    }

    if (p) {
        t = [];
        t.push("Collection ");
        t.push(["strong", model.sel.collectioncode]);
        t.push(" contains ");
        t.push(f_large(p.x) + " " + stat.xlabel);
        t.push(" and ");
        t.push(f_large(p.y) + " " + stat.ylabel);
        t.push(".");
        textmaker(this.info.append("p"), t);

        t = [];
        if (p.fraction <= config.p_threshold) {
            t.push("Only approx. ");
        } else {
            t.push(" Approx. ");
        }
        t.push(["strong", f_fraction(100 * p.fraction) + "%"]);
        t.push(" of random collections with ");
        t.push(f_large(p.x) + " " + stat.xlabel);
        t.push(" contain ");
        t.push(p.side === "below" ? "at most" : "at least");
        t.push(" ");
        t.push(f_large(p.y) + " " + stat.ylabel);
        t.push(".");
        textmaker(this.info.append("p"), t);

        t = [];
        if (p.fraction > config.p_threshold) {
            t.push("This seems to be a fairly typical collection.");
        } else {
            if (p.fdr > config.fdr_threshold) {
                t.push("This finding is probably not interesting:");
                t.push(" the false discovery rate is larger than ");
                t.push(config.fdr_threshold);
                t.push(".");
            } else {
                t.push("This finding is probably interesting:");
                t.push(" the false discovery rate is approx. ");
                t.push(["strong", f_fraction(p.fdr)]);
                t.push(".");
            }
        }
        textmaker(this.info.append("p"), t);
    }
};

View.prototype.ev_resize = function() {
    if (this.plot) {
        this.plot.recalc_plot();
    }
};


//// Controller

var Controller = function(model) {
    this.model = model;
    this.view = new View(this);
    this.expected_hash = null;
    this.fields = [
        {
            menu: '<i>types</i>2',
            key: 'pagecode',
            get: model.get_pagecodes.bind(model),
            invalidates: [
                'page',
                'curves', 'points', 'results', 'selection',
                'sample_table', 'token_table', 'context_table'            ]
        },
        {
            menu: 'Corpus',
            key: 'corpuscode',
            get: model.get_corpuscodes.bind(model),
            invalidates: [
                'datasetcode', 'groupcode', 'collectioncode', 'samplecode', 'tokencode',
                'curves', 'points', 'selection',
                'sample_table', 'token_table', 'context_table'
            ]
        },
        {
            menu: 'Dataset',
            key: 'datasetcode',
            get: model.get_datasetcodes.bind(model),
            invalidates: [
                'tokencode',
                'curves', 'points', 'selection',
                'sample_table', 'token_table', 'context_table'
            ]
        },
        {
            menu: 'Group',
            key: 'groupcode',
            get: model.get_groupcodes.bind(model),
            invalidates: [
                'collectioncode', 'samplecode', 'tokencode',
                'points', 'selection'
            ]
        },
        {
            menu: 'Collection',
            key: 'collectioncode',
            get: model.get_collectioncodes.bind(model),
            invalidates: [
                'samplecode', 'tokencode',
                'points', 'selection',
                'sample_table', 'token_table', 'context_table'
            ]
        },
        {
            menu: 'Statistics',
            key: 'statcode',
            get: model.get_statcodes.bind(model),
            invalidates: [
                'curves', 'points', 'selection'
            ]
        },
        {
            key: 'samplecode',
            invalidates: [
                'tokencode',
                'selection',
                'context_table'
            ]
        },
        {
            key: 'tokencode',
            invalidates: [
                'selection',
                'context_table'
            ]
        }
    ];
    d3.select(window)
        .on('resize', this.view.ev_resize.bind(this.view))
        .on('hashchange', this.ev_hashchange.bind(this));
};

Controller.prototype.update_sel = function(changes) {
    if (changes.force || changes.invalid.page) {
        this.view.set_page(this.model);
    }
    if (changes.force || changes.invalid.curves) {
        this.view.set_curves(this.model);
    }
    if (changes.force || changes.invalid.points) {
        this.view.set_points(this.model);
    }
    if (changes.force || changes.invalid.results) {
        this.view.set_results(this.model);
    }
    if (changes.force || changes.invalid.sample_table) {
        this.view.set_samples(this.model);
    }
    if (changes.force || changes.invalid.token_table) {
        this.view.set_tokens(this.model);
    }
    if (changes.force || changes.invalid.context_table) {
        this.view.set_context(this.model);
    }
    if (changes.force || changes.invalid.selection) {
        this.view.set_info(this.model);
        this.view.set_sel(this.model);
    }
};

Controller.prototype.set_sel_raw = function(old, x) {
    for (var i = 0; i < this.fields.length; ++i) {
        var f = this.fields[i];
        var k = f.key;
        if (k in x) {
            this.model.sel[k] = x[k];
        } else {
            this.model.sel[k] = old[k];
        }
    }
};

Controller.prototype.find_changed = function(old) {
    var changes = {
        changed: {},
        invalid: {},
        count: 0
    };
    for (var i = 0; i < this.fields.length; ++i) {
        var f = this.fields[i];
        var k = f.key;
        if (this.model.sel[k] !== old[k]) {
            changes.changed[k] = true;
            ++changes.count;
            for (var j = 0; j < f.invalidates.length; ++j) {
                changes.invalid[f.invalidates[j]] = true;
            }
        }
    }
    return changes;
};

Controller.prototype.update_inputs = function(changes) {
    var ctrl = this;
    var model = this.model;
    var mainmenu = d3.select("#mainmenu");
    mainmenu.selectAll("*").remove();

    var update_one = function(f) {
        if (!f.menu) {
            return;
        }
        var k = f.key;
        var values = f.get();

        var menutitle = mainmenu.append("div");
        var submenu = mainmenu.append("div");
        menutitle.classed("title", true).html(f.menu);
        submenu.classed("submenu", true);
        var sel = submenu.selectAll("div").data(values)
            .enter().append("div");
        sel.classed("menuitem", true);
        sel.classed("active", function(d) { return model.sel[k] === d.code; });
        sel.classed("inactive", function(d) { return model.sel[k] !== d.code; });
        sel.text(function(d) {
            if (d === null) {
                return "none";
            } else {
                return d.label;
            }
        });
        sel.on('click', function(d) {
            var x = {};
            x[k] = d.code;
            ctrl.recalc_sel(x);
        });
    };
    for (var i = 0; i < this.fields.length; ++i) {
        update_one(this.fields[i]);
    }
};

Controller.prototype.update_hash = function() {
    var x = [];
    for (var i = 0; i < this.fields.length; ++i) {
        x.push(hash_encode(this.model.sel[this.fields[i].key]));
    }
    this.expected_hash = x.join("/");
    location.hash = this.expected_hash;
};

Controller.prototype.recalc_sel = function(x, force) {
    var model = this.model;
    var old = model.sel;
    model.sel = {};
    this.set_sel_raw(old, x);
    model.fix_sel();
    var changes = this.find_changed(old);
    changes.force = force;
    if (!changes.force && !changes.count) {
        return;
    }
    this.update_inputs(changes);
    this.update_sel(changes);
    this.update_hash();
};

Controller.prototype.data = function(data) {
    this.model.set_data(data);
    this.recalc_sel(this.parse_hash(), true);
};

Controller.prototype.ev_point_click = function(d) {
    if (this.model.all_set(d)) {
        this.recalc_sel({ collectioncode: null });
    } else {
        this.recalc_sel(d);
    }
};

Controller.prototype.ev_result_cell_click = function(d) {
    if (this.model.all_set(d.row)) {
        this.recalc_sel({ groupcode: null });
    } else {
        this.recalc_sel(d.row);
    }
};

Controller.prototype.ev_sample_cell_click = function(d) {
    if (this.model.all_set(d.row)) {
        this.recalc_sel({ samplecode: null });
    } else {
        this.recalc_sel(d.row);
    }
};

Controller.prototype.ev_token_cell_click = function(d) {
    if (this.model.all_set(d.row)) {
        this.recalc_sel({ tokencode: null });
    } else {
        this.recalc_sel(d.row);
    }
};

Controller.prototype.parse_hash = function() {
    var x = this.try_parse_hash();
    if (x) {
        return x;
    } else {
        return {};
    }
};

Controller.prototype.try_parse_hash = function() {
    var hash = location.hash;
    if (hash.length <= 1) {
        return null;
    }
    hash = hash.substring(1);
    if (hash === this.expected_hash) {
        return null;
    }
    var f = location.hash.substring(1).split('/');
    var x = {};
    for (var i = 0; i < f.length; ++i) {
        if (i < this.fields.length) {
            x[this.fields[i].key] = hash_decode(f[i]);
        }
    }
    return x;
};

Controller.prototype.ev_hashchange = function() {
    var x = this.try_parse_hash();
    if (x) {
        this.recalc_sel(x);
    }
};

//// Model: Database

var Database = function(data) {
    this.data = data;
    this.setup_group_maps();
    this.setup_corpuscodes();
    this.setup_datasetcodes();
    this.setup_statcodes();
    this.setup_results();
    this.setup_samples();
    this.setup_collections();
    this.setup_tokens();
    this.setup_context();
};

Database.prototype.setup_group_maps = function() {
    this.group_map = {};
    this.group_map_map = {};
    this.group_reverse_map = {};
    this.group_list = {};
    for (var corpuscode in this.data.collection) {
        this.setup_group_map(corpuscode);
    }
};

Database.prototype.setup_group_map = function(corpuscode) {
    var all = [];
    var other = [];
    var x = {};
    var collections = this.data.collection[corpuscode];
    for (var collectioncode in collections) {
        var collection = collections[collectioncode];
        if (collection.groupcode) {
            push1(x, collection.groupcode, collectioncode);
        } else {
            other.push(collectioncode);
        }
        all.push(collectioncode);
    }

    this.group_map[corpuscode] = {};
    this.group_map_map[corpuscode] = {};
    this.group_reverse_map[corpuscode] = {};
    this.group_list[corpuscode] = [];
    this.add_group(corpuscode, 'all', 'all', all);
    var normal_groups = Object.keys(x);
    normal_groups.sort();
    for (var i = 0; i < normal_groups.length; ++i) {
        var groupcode = normal_groups[i];
        this.add_group(corpuscode, '.' + groupcode, groupcode, x[groupcode]);
    }
    if (other.length > 0 && other.length < all.length) {
        this.add_group(corpuscode, 'other', 'orher', other);
    }
};

Database.prototype.add_group = function(corpuscode, groupcode, grouplabel, collections) {
    collections.sort();
    this.group_list[corpuscode].push({code: groupcode, label: grouplabel});
    this.group_map[corpuscode][groupcode] = collections;
    this.group_map_map[corpuscode][groupcode] = {};
    for (var i = 0; i < collections.length; ++i) {
        var collectioncode = collections[i];
        this.group_map_map[corpuscode][groupcode][collectioncode] = true;
        this.group_reverse_map[corpuscode][collectioncode] = groupcode;
    }
};

Database.prototype.setup_corpuscodes = function() {
    this.corpuscodes = Object.keys(this.data.corpus);
    this.corpuscodes.sort();
};

Database.prototype.setup_datasetcodes = function() {
    this.datasetcodes = {};
    for (var corpuscode in this.data.dataset) {
        var l = Object.keys(this.data.dataset[corpuscode]);
        l.sort();
        this.datasetcodes[corpuscode] = l;
    }
};

Database.prototype.setup_statcodes = function() {
    this.statcodes = [];
    this.statcode_map = {};
    for (var i = 0; i < config.statcodes.length; ++i) {
        var statcode = config.statcodes[i];
        if (this.data.stat[statcode]) {
            var x = this.data.stat[statcode].x;
            var y = this.data.stat[statcode].y;
            var xlabel = this.data.label[x].labeltext;
            var ylabel = this.data.label[y].labeltext;
            var stat = {
                code: statcode,
                x: x,
                y: y,
                xlabel: xlabel,
                ylabel: ylabel,
                label: ylabel + " / " + xlabel
            };
            this.statcodes.push(stat);
            this.statcode_map[statcode] = stat;
        }
    }
};

Database.prototype.setup_results = function() {
    var indexes = [];
    for (var i in this.data.result_q) {
        indexes.push(+i);
    }
    sort_numbers(indexes);
    var qq = null;
    this.point_ordered = [];
    for (var j = 0; j < indexes.length; ++j) {
        var r = this.data.result_q[indexes[j]];
        if (qq === null || qq < r.q) {
            qq = r.q;
        }
        var p = this.data.result_p[r.corpuscode][r.datasetcode][r.collectioncode][r.statcode];
        if (!p.side) {
            p.fdr = qq;
            p.side = r.side;
            p.fraction = p[r.side] / p.total;
            p.corpuscode = r.corpuscode;
            p.datasetcode = r.datasetcode;
            p.collectioncode = r.collectioncode;
            p.statcode = r.statcode;
            p.groupcode = this.group_reverse_map[r.corpuscode][r.collectioncode];
            this.point_ordered.push(p);
        }
    }
    this.num_tests = indexes.length;
};

Database.prototype.setup_samples = function() {
    for (var corpuscode in this.data.sample) {
        var corpus = this.data.corpus[corpuscode];
        var samples = this.data.sample[corpuscode];
        var wc = 0;
        var sc = 0;
        for (var samplecode in samples) {
            var sample = samples[samplecode];
            sample.corpuscode = corpuscode;
            sample.samplecode = samplecode;
            wc += sample.wordcount;
            sc += 1;
        }
        corpus.wordcount = wc;
        corpus.samplecount = sc;
    }
};

Database.prototype.setup_collections = function() {
    var x = this.data.sample_collection;
    var y = {};
    this.sample_collection_map = y;
    for (var corpuscode in x) {
        var xx = x[corpuscode];
        var yy = {};
        y[corpuscode] = yy;
        for (var collectioncode in xx) {
            var xxx = xx[collectioncode];
            var yyy = {};
            yy[collectioncode] = yyy;
            for (var i = 0; i < xxx.length; ++i) {
                var samplecode = xxx[i];
                yyy[samplecode] = true;
            }
        }
    }
};

Database.prototype.setup_tokens_sample1 = function(corpuscode, datasetcode) {
    var dataset = this.data.dataset[corpuscode][datasetcode];
    dataset.tokencount = {};
    dataset.samplecount = {};
    for (var samplecode in this.data.sample[corpuscode]) {
        var sample = this.data.sample[corpuscode][samplecode];
        var s = {
            corpuscode: corpuscode,
            datasetcode: datasetcode,
            samplecode: samplecode,
            description: sample.description,
            wordcount: sample.wordcount,
            link: sample.link,
            tokencount: {}
        };
        set3(this.sample_data, corpuscode, datasetcode, samplecode, s);
        var t = get3list(this.data.token, corpuscode, datasetcode, samplecode);
        for (var tokencode in t) {
            var token = t[tokencode];
            if (token.tokencount) {
                add1(dataset.tokencount, tokencode, token.tokencount);
                add1(dataset.samplecount, tokencode, 1);
                add1(s.tokencount, tokencode, token.tokencount);
            }
        }
    }
};

Database.prototype.setup_tokens_sample2 = function(corpuscode, datasetcode) {
    var dataset = this.data.dataset[corpuscode][datasetcode];
    for (var samplecode in this.data.sample[corpuscode]) {
        var s = this.sample_data[corpuscode][datasetcode][samplecode];
        s.unique = [];
        s.hapaxes = 0;
        s.tokens = 0;
        s.types = 0;
        for (var tokencode in s.tokencount) {
            var gc = dataset.tokencount[tokencode];
            var sc = s.tokencount[tokencode];
            s.tokens += sc;
            s.types += 1;
            if (gc === 1) {
                s.hapaxes += 1;
            }
            if (gc === sc) {
                var l = get4(this.data.tokeninfo, corpuscode, datasetcode, tokencode, "shortlabel");
                if (!l) {
                    l = tokencode;
                }
                s.unique.push(l);
            }
        }
    }
};

Database.prototype.setup_tokens_collection1 = function(corpuscode, datasetcode) {
    var dataset = this.data.dataset[corpuscode][datasetcode];
    dataset.collection_tokencount = {};
    dataset.collection_samplecount = {};
    for (var collectioncode in this.data.collection[corpuscode]) {
        var xt = {};
        var xs = {};
        dataset.collection_tokencount[collectioncode] = xt;
        dataset.collection_samplecount[collectioncode] = xs;
        var sc = this.data.sample_collection[corpuscode][collectioncode];
        for (var i = 0; i < sc.length; ++i) {
            var samplecode = sc[i];
            var s = this.sample_data[corpuscode][datasetcode][samplecode];
            for (var tokencode in s.tokencount) {
                add1(xt, tokencode, s.tokencount[tokencode]);
                add1(xs, tokencode, 1);
            }
        }
    }
};

Database.prototype.setup_tokens_dataset1 = function(corpuscode, datasetcode) {
    var dataset = this.data.dataset[corpuscode][datasetcode];
    dataset.hapaxes = 0;
    dataset.tokens = 0;
    dataset.types = 0;
    for (var tokencode in dataset.tokencount) {
        var count = dataset.tokencount[tokencode];
        dataset.tokens += count;
        dataset.types += 1;
        if (count === 1) {
            dataset.hapaxes += 1;
        }
    }
};

Database.prototype.setup_tokens = function() {
    this.sample_data = {};
    for (var corpuscode in this.data.token) {
        for (var datasetcode in this.data.dataset[corpuscode]) {
            this.setup_tokens_sample1(corpuscode, datasetcode);
            this.setup_tokens_sample2(corpuscode, datasetcode);
            this.setup_tokens_collection1(corpuscode, datasetcode);
            this.setup_tokens_dataset1(corpuscode, datasetcode);
        }
    }
};

Database.prototype.setup_context = function() {
    for (var corpuscode in this.data.context) {
        var t1 = this.data.context[corpuscode];
        for (var datasetcode in t1) {
            var t2 = t1[datasetcode];
            for (var samplecode in t2) {
                var t3 = t2[samplecode];
                for (var tokencode in t3) {
                    var t4 = t3[tokencode];
                    var tokeninfo = get3(this.data.tokeninfo, corpuscode, datasetcode, tokencode);
                    for (var i = 0; i < t4.length; ++i) {
                        var context = t4[i];
                        context.corpuscode = corpuscode;
                        context.datasetcode = datasetcode;
                        context.samplecode = samplecode;
                        context.tokencode = tokencode;
                        context.shortlabel = tokencode;
                        context.longlabel = tokencode;
                        if (tokeninfo && tokeninfo.shortlabel) {
                            context.shortlabel = tokeninfo.shortlabel;
                        }
                        if (tokeninfo && tokeninfo.longlabel) {
                            context.longlabel = tokeninfo.longlabel;
                        }
                        if (context.before) {
                            var words = context.before.split(/\s+/);
                            words.reverse();
                            context.before_sort = words.join(" ").trim().toLowerCase();
                        }
                        if (context.after) {
                            context.after_sort = context.after.trim().toLowerCase();
                        }
                        if (context.word) {
                            context.word_sort = context.word.trim().toLowerCase();
                        }
                    }
                }
            }
        }
    }
};

Database.prototype.get_curves = function(sel) {
    var curves = {
        maxx: 1,
        maxy: 1,
        data: []
    };
    var input = get3(this.data.result_curve, sel.corpuscode, sel.datasetcode, sel.statcode);
    if (!input) {
        return curves;
    }
    var levels = [];
    for (var level in input) {
        levels.push(+level);
    }
    sort_numbers(levels);
    for (var i = 0; i < levels.length; ++i) {
        this.get_one_curve(curves, input, levels[i]);
    }
    return curves;
};

Database.prototype.get_one_curve = function(curves, input, level) {
    var curve_lower = input[level].lower.id;
    var curve_upper = input[level].upper.id;
    var data_lower = this.data.result_curve_point[curve_lower];
    var data_upper = this.data.result_curve_point[curve_upper];
    var i = 0;
    var j = 0;
    var x = 0;
    var y0 = 0;
    var y1 = 0;
    var maxy = 0;
    var data = [];
    while (i < data_lower.length || j < data_upper.length) {
        var igood = false;
        var jgood = false;
        if (i === data_lower.length) {
            jgood = true;
        } else if (i === data_lower.length) {
            igood = true;
        } else {
            igood = (data_lower[i].x <= data_upper[j].x);
            jgood = (data_lower[i].x >= data_upper[j].x);
        }
        if (igood) {
            x = data_lower[i].x;
            y0 = data_lower[i].y;
            ++i;
        }
        if (jgood) {
            x = data_upper[j].x;
            y1 = data_upper[j].y;
            ++j;
        }
        data.push({x: x, y0: y0, y1: y1});
        if (y1 > maxy) {
            maxy = y1;
        }
    }
    if (x > curves.maxx) {
        curves.maxx = x;
    }
    if (maxy > curves.maxy) {
        curves.maxy = maxy;
    }
    curves.data.push({level: level, data: data});
};

Database.prototype.get_points = function(sel) {
    var points = [];
    var collections = get2list(this.group_map, sel.corpuscode, sel.groupcode);
    for (var i = 0; i < collections.length; ++i) {
        var collectioncode = collections[i];
        var input = get4(this.data.result_p, sel.corpuscode, sel.datasetcode, collectioncode, sel.statcode);
        if (input) {
            points.push({
                collectioncode: collectioncode,
                x: input.x,
                y: input.y,
                above: input.above / input.total,
                below: input.below / input.total,
                sel: (collectioncode === sel.collectioncode)
            });
        }
    }
    return points;
};

//// Model

var Model = function() {
    this.db = null;
    this.sel = {
        pagecode: null,
        corpuscode: null,
        datasetcode: null,
        groupcode: null,
        collectioncode: null,
        statcode: null,
        samplecode: null,
        tokencode: null
    };
    this.pagecodes = [
        { label: "Overview", code: null },
        { label: "Plot", code: "plot" },
        { label: "Samples", code: "samples" },
        { label: "Types", code: "types" }
    ];
    this.pagecodemap = {};
    for (var i = 0; i < this.pagecodes.length; ++i) {
        var p = this.pagecodes[i];
        if (p.code) {
            this.pagecodemap[p.code] = true;
        }
    }
};

Model.prototype.all_set = function(x) {
    for (var key in x) {
        if (key in this.sel && x[key] !== this.sel[key]) {
            return false;
        }
    }
    return true;
};

Model.prototype.fix_sel = function() {
    var sel = this.sel;
    var data = this.db.data;
    if (!sel.pagecode || !(sel.pagecode in this.pagecodemap)) {
        sel.pagecode = null;
    }
    if (!sel.corpuscode || !(sel.corpuscode in data.corpus)) {
        sel.corpuscode = get0first(this.db.corpuscodes);
    }
    if (!sel.datasetcode || !(sel.datasetcode in get1obj(data.dataset, sel.corpuscode))) {
        sel.datasetcode = get1first(this.db.datasetcodes, sel.corpuscode);
    }
    if (sel.groupcode && !(sel.groupcode in get1obj(this.db.group_map, sel.corpuscode))) {
        sel.groupcode = null;
    }
    if (sel.collectioncode && !(sel.collectioncode in get2obj(this.db.group_map_map, sel.corpuscode, sel.groupcode))) {
        sel.collectioncode = null;
    }
    if (sel.collectioncode) {
        if (sel.samplecode && !(sel.samplecode in get2obj(this.db.sample_collection_map, sel.corpuscode, sel.collectioncode))) {
            sel.samplecode = null;
        }
    } else {
        if (sel.samplecode && !(sel.samplecode in get1obj(this.db.data.sample, sel.corpuscode))) {
            sel.samplecode = null;
        }
    }
    if (sel.samplecode && sel.tokencode) {
        sel.tokencode = null;
    }
    if (!sel.statcode || !(sel.statcode in this.db.statcode_map)) {
        sel.statcode = get1(get0first(this.db.statcodes), "code");
    }
};

Model.prototype.set_data = function(data) {
    this.db = new Database(data);
};

Model.prototype.get_curves = function() {
    return this.db.get_curves(this.sel);
};

Model.prototype.get_points = function() {
    return this.db.get_points(this.sel);
};

var add_structure = function(x) {
    if (x) {
        return {label: x, code: x};
    } else {
        return {label: "none", code: null};
    }
};

var just_none = [add_structure(null)];

Model.prototype.get_pagecodes = function() {
    return this.pagecodes;
};

Model.prototype.get_corpuscodes = function() {
    return this.db.corpuscodes.map(add_structure);
};

Model.prototype.get_datasetcodes = function() {
    return get1list(this.db.datasetcodes, this.sel.corpuscode).map(add_structure);
};

Model.prototype.get_groupcodes = function() {
    if (!this.sel.corpuscode) {
        return just_none;
    }
    return this.db.group_list[this.sel.corpuscode].concat(just_none);
};

Model.prototype.get_collectioncodes = function() {
    if (!this.sel.corpuscode || !this.sel.groupcode) {
        return just_none;
    }
    return just_none.concat(this.db.group_map[this.sel.corpuscode][this.sel.groupcode].map(add_structure));
};

Model.prototype.get_statcodes = function() {
    return this.db.statcodes;
};

Model.prototype.get_point = function() {
    var sel = this.sel;
    return get4(this.db.data.result_p, sel.corpuscode, sel.datasetcode, sel.collectioncode, sel.statcode);
};

Model.prototype.get_stat = function() {
    var sel = this.sel;
    return get1(this.db.statcode_map, sel.statcode);
};

Model.prototype.get_corpus = function() {
    var sel = this.sel;
    return get1(this.db.data.corpus, sel.corpuscode);
};

Model.prototype.get_dataset = function() {
    var sel = this.sel;
    return get2(this.db.data.dataset, sel.corpuscode, sel.datasetcode);
};

Model.prototype.get_samples = function() {
    var sel = this.sel;
    if (sel.corpuscode && sel.datasetcode) {
        var m = this.db.sample_data[sel.corpuscode][sel.datasetcode];
        var l;
        if (sel.collectioncode) {
            l = this.db.data.sample_collection[sel.corpuscode][sel.collectioncode];
        } else {
            l = Object.keys(m);
        }
        return l.map(function(samplecode) {
            return m[samplecode];
        });
    } else {
        return [];
    }
};

Model.prototype.get_tokens = function() {
    var sel = this.sel;
    var r = [];
    var dataset = get2(this.db.data.dataset, sel.corpuscode, sel.datasetcode);
    if (!dataset) {
        return r;
    }
    var c_tokencount = get1(dataset.collection_tokencount, sel.collectioncode);
    var c_samplecount = get1(dataset.collection_samplecount, sel.collectioncode);
    var tokencodes = Object.keys(dataset.tokencount);
    tokencodes.sort();
    for (var i = 0; i < tokencodes.length; ++i) {
        var tokencode = tokencodes[i];
        var tokeninfo = get3(this.db.data.tokeninfo, sel.corpuscode, sel.datasetcode, tokencode);
        var t = {
            corpuscode: sel.corpuscode,
            datasetcode: sel.datasetcode,
            tokencode: tokencode,
            shortlabel: tokencode,
            longlabel: tokencode
        };
        t.tokencount = dataset.tokencount[tokencode];
        t.samplecount = dataset.samplecount[tokencode];
        if (sel.collectioncode) {
            t.tokencount_collection = get1num(c_tokencount, tokencode);
            t.tokencount_fraction = t.tokencount_collection / t.tokencount;
            t.tokencount_score = calc_score(t.tokencount_collection, t.tokencount);
            t.samplecount_collection = get1num(c_samplecount, tokencode);
            t.samplecount_fraction = t.samplecount_collection / t.samplecount;
            t.samplecount_score = calc_score(t.samplecount_collection, t.samplecount);
        }
        if (tokeninfo && tokeninfo.shortlabel) {
            t.shortlabel = tokeninfo.shortlabel;
        }
        if (tokeninfo && tokeninfo.longlabel) {
            t.longlabel = tokeninfo.longlabel;
        }
        r.push(t);
    }
    return r;
};

Model.prototype.get_context = function() {
    var sel = this.sel;
    if (!sel.samplecode && !sel.tokencode) {
        return [];
    }
    var data = this.db.data;
    var t = get2(data.context, sel.corpuscode, sel.datasetcode);

    var r = [];
    var samplecodes = [];
    if (sel.samplecode) {
        samplecodes = [sel.samplecode];
    } else {
        samplecodes = Object.keys(this.db.data.sample[sel.corpuscode]);
    }
    for (var i = 0; i < samplecodes.length; ++i) {
        var tt = get1(t, samplecodes[i]);
        if (!tt) {
        } else if (sel.tokencode) {
            r = r.concat(get1list(tt, sel.tokencode));
        } else {
            for (var tokencode in tt) {
                r = r.concat(get1list(tt, tokencode));
            }
        }
    }
    return r;
};


//// main

return new Controller(new Model());
}());
