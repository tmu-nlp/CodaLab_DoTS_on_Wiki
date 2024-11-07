library(ggplot2)
library(reshape2)
library(ggpubr)
# library(rlang)
# aes(x = !!sym(paste(prefix, suffix, sep = '.')), fill = set)

stat_path <-'../tmp/stat/'
svg_path <- '../tmp/svg/'
pdf_path <- '../tmp/pdf/'

load_corp <- function(lang, ds) {
    fname <- paste0(stat_path, lang, '.', ds, '.csv')
    data <- read.csv(fname)
    data$set <- rep(ds, nrow(data))
    data
}

mkset <- function(lang, d) {
    if (lang == 'en') {
        d$set <- factor(d$set, levels = c('train', 'val', 'test_id', 'test_ood'), labels = c('Train', 'Dev.', 'Test\nin-domain', 'Test\nout-of-domain'))
    } else if (lang == 'de') {
        d$set <- factor(d$set, levels = c('train', 'validation', 'test'), labels = c('Train', 'Dev.', 'Test'))
    } else {
        d$set <- factor(d$set, levels = c('train', 'valid', 'test'), labels = c('Train', 'Dev.', 'Test'))
    }
    d[order(d$set), ]
}

data <- rbind(load_corp('ja', 'train'), load_corp('ja', 'valid'), load_corp('ja', 'test'))
data <- mkset('ja', data)

ds_name <- function(lang) {
    if (lang == 'en') {
        ds <- 'SWiPE'
    } else if (lang == 'de') {
        ds  <- 'Klexikon'
    } else if (lang == 'ja') {
        ds <- 'JADOS'
    }
    ds
}

n_length <- function(lang, data, is_density) {
    data <- melt(data, id.vars = c('title', 'set'), measure.vars = c('s.word', 's.sent', 'r.word', 'r.sent'), variable.name = 'cat', value.name = 'length')
    # print(head(data))
    # bi <- strsplit(as.character(data$cat), '\\.')
    # print(bi)

    # data$side        <- factor(sapply(bi, `[`, 1), levels = c('s', 'r'),       labels = c('Source', 'Target'))
    # data$granularity <- factor(sapply(bi, `[`, 2), levels = c('word', 'sent'), labels = c('Word', 'Sentence'))

    data$cat <- factor(data$cat, levels = c('s.word', 's.sent', 'r.word', 'r.sent'), labels = c('Source Words', 'Source Sentences', 'Target Words', 'Target Sentences'))

    p <- ggplot(data, aes(x = length, fill = set))
    if (is_density) {
        p <- p + geom_density(alpha = 0.5)
        p <- p + theme(
            axis.ticks.y = element_blank(),
            axis.text.y = element_blank()
        )
        y <- 'Density'
    } else {
        p <- p + geom_bar(position = "dodge2")
        y <- 'Count'
    }

    p <- p + facet_wrap( ~ cat, scale = 'free')
    p <- p + labs(x = 'Count', y = y, fill = paste0(ds_name(lang), '\n', 'Data split'))
    p <- p + theme(
        axis.title.x = element_blank(),
        legend.spacing = unit(0, "pt"),
        legend.margin = margin(t = 0, r = 0, b = 0, l = 0),
        legend.position = "top",
        legend.direction = "horizontal"
    #     legend.position = "inside",
    #     legend.position.inside = c(0.88, 0.7),
    #     legend.background = element_rect(fill = alpha("white", 0)))
    )
    p

    f <- paste(lang, y, sep = '.')
    ggsave(paste0(pdf_path, f, '.pdf'), height = 2.9, width = 5)
    ggsave(paste0(svg_path, f, '.svg'), height = 2.9, width = 5.5)
}

vals <- c(T, F)
for (d in vals) {
    n_length('ja', subset(data, s.word < 1500 & s.sent < 80), d)
}

print(paste('JADOS:'))
arr <- data$s.word
print(paste(' s.word', mean(arr), sd(arr)))
arr <- data$r.word
print(paste(' r.word', mean(arr), sd(arr)))
arr <- data$s.sent
print(paste(' s.sent', mean(arr), sd(arr)))
arr <- data$r.sent
print(paste(' r.sent', mean(arr), sd(arr)))

.data <- rbind(load_corp('en', 'train'), load_corp('en', 'val'), load_corp('en', 'test_id'), load_corp('en', 'test_ood'))
.data <- mkset('en', .data)

print(paste('SWiPE:'))
arr <- .data$s.word
print(paste(' s.word', mean(arr), sd(arr)))
arr <- .data$r.word
print(paste(' r.word', mean(arr), sd(arr)))
arr <- .data$s.sent
print(paste(' s.sent', mean(arr), sd(arr)))
arr <- .data$r.sent
print(paste(' r.sent', mean(arr), sd(arr)))
.data <- subset(.data, r.word < 250 & r.sent < 20 & s.word < 500 & s.sent < 500)

for (d in vals) {
    n_length('en', .data, d)
}

.data <- rbind(load_corp('de', 'train'), load_corp('de', 'validation'), load_corp('de', 'test'))
.data <- mkset('de', .data)
print(paste('Klexikon:'))
arr <- .data$s.word
print(paste(' s.word', mean(arr), sd(arr)))
arr <- .data$r.word
print(paste(' r.word', mean(arr), sd(arr)))
arr <- .data$s.sent
print(paste(' s.sent', mean(arr), sd(arr)))
arr <- .data$r.sent
print(paste(' r.sent', mean(arr), sd(arr)))

for (d in vals) {
    n_length('de', .data, d)
}

genre <- function(data) {
    p <- ggplot(data, aes(x = wiki)) 
    p <- p + geom_bar()
    # p <- p + geom_text(aes(label = after_stat(count)), stat = "count", vjust = -1.5, colour = "white")
    p <- p + facet_wrap(~set, scale = 'free_y')
    p <- p + labs(x = 'Wikipedia Article Type', y = 'Count')
    p

    ggsave(paste0(pdf_path, 'ja.genre.pdf'), height = 2.3, width = 5.5)
    ggsave(paste0(svg_path, 'ja.genre.svg'), height = 2.3, width = 5.5)
}

genre(data)

edit <- function(data) {
    levels <- c('D', 'E', 'M', 'I', 'S')
    labels <- c('Delete', 'Edit', 'Merge', 'Insert', 'Split')
    data <- melt(data = data, id.vars = c("set"), measure.vars = levels)
    data$variable <- factor(data$variable, levels = levels, labels = labels)
    # print(head(data))
    p <- ggplot(data, aes(x = set, fill = variable, weight = value))
    p <- p + geom_bar(position = "fill")
    p <- p + scale_y_continuous(labels = scales::percent)
    p <- p + theme(axis.title = element_blank())
    p <- p + scale_fill_discrete(name = 'Operation')
    p
    ggsave(paste0(pdf_path, 'ja.edit.pdf'), height = 2.3, width = 5.5)
    ggsave(paste0(svg_path, 'ja.edit.svg'), height = 2.3, width = 5.5)
}

edit(data)

del.pos <- function(lang) {
    data <- read.csv(paste0(stat_path, lang, '.del.pos.csv'))
    data <- mkset(lang, data)
    data$ratio <- data$pos / (data$total - 1)

    p <- ggplot(data, aes(ratio, fill = set))
    p <- p + geom_density(alpha = 0.5)
    p <- p + labs(x = 'Normalized Positions of Deleted Sentences across Documents', y = 'Density', fill = paste0(ds_name(lang), ' Data split'))
    p <- p + scale_x_continuous(breaks = c(0, 0.5, 1), labels = c('Start', 'Middle', 'End'))
    p <- p + theme(
        axis.ticks.y = element_blank(),
        axis.text.y = element_blank()
    )

    # p <- ggplot(data, aes(ratio, total))
    # p <- p + geom_point()
    p
}

del.ratio <- function(lang) {
    data <- read.csv(paste0(stat_path, lang, '.del.ratio.csv'))
    data <- subset(data, total < 300)
    data <- mkset(lang, data)
    p <- ggplot(data, aes(total, 1 - ratio / total, color = set))
    if (lang == 'ja') {
        p <- p + geom_point(alpha = I(0.2))
    } else {
        p <- p + geom_point(alpha = I(0.2), position = position_jitter(width = 0.22, height = 0.02))
        p <- p + geom_smooth(se = F)
    }
    p <- p + scale_y_continuous(limits = c(-0.02, 1.02), breaks = seq(0, 1, 0.25), labels = c('0%', '25%', '50%', '75%', '100%'))
    p <- p + labs(x = '# of Sentences in Source Documents', y = 'Remnant Ratio', color = paste0(ds_name(lang), ' Data split'))
    p
}

for (lang in c('ja', 'en')) {
    ggarrange(del.pos(lang), del.ratio(lang), nrow = 2, common.legend = TRUE, heights = c(0.45, 0.55))
    ggsave(paste0(pdf_path, lang, '.Deletion.pdf'), height = 4, width = 5.5)
    ggsave(paste0(svg_path, lang, '.Deletion.svg'), height = 3.5, width = 5.5)
}



category <- function(data) {
    library(showtext)
    showtext_auto(enable = TRUE)
    size <- 0.46
    # data$set <- factor(data$set, levels = c('test', 'valid', 'train'), labels = c('Test', 'Dev.', 'Train'))
    p <- ggplot(data, aes(x = set, fill = category))
    p <- p + geom_bar(position = "fill")
    p <- p + scale_y_continuous(labels = scales::percent)
    # p <- p + scale_x_discrete(limits = rev)
    p <- p + theme(
        axis.title = element_blank(),
        legend.text=element_text(size = 7),
        legend.key.height = unit(size, "cm"),
        legend.key.width  = unit(size, "cm"))
    p <- p + scale_fill_discrete(name = 'Category')
    p
    ggsave(paste0(pdf_path, 'ja.category.pdf'), height = 2.3, width = 5.5)
    ggsave(paste0(svg_path, 'ja.category.svg'), height = 2.3, width = 5.5)
}

category(data)