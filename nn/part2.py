import sys
import os.path
import cv2

from helpers import *

from mobject.tex_mobject import TexMobject
from mobject import Mobject, Group
from mobject.image_mobject import ImageMobject
from mobject.vectorized_mobject import *

from animation.animation import Animation
from animation.transform import *
from animation.simple_animations import *
from animation.playground import *
from animation.continual_animation import *
from topics.geometry import *
from topics.characters import *
from topics.functions import *
from topics.fractals import *
from topics.number_line import *
from topics.combinatorics import *
from topics.numerals import *
from topics.three_dimensions import *
from topics.objects import *
from topics.probability import *
from topics.complex_numbers import *
from topics.graph_scene import *
from topics.common_scenes import *
from scene import Scene
from scene.reconfigurable_scene import ReconfigurableScene
from scene.zoomed_scene import *
from camera import Camera
from mobject.svg_mobject import *
from mobject.tex_mobject import *

from nn.network import *
from nn.part1 import *

POSITIVE_COLOR = BLUE
NEGATIVE_COLOR = RED

def get_training_image_group(train_in, train_out):
    image = MNistMobject(train_in)
    image.scale_to_fit_height(1)
    arrow = Vector(RIGHT, color = BLUE, buff = 0)
    output = np.argmax(train_out)
    output_tex = TexMobject(str(output)).scale(1.5)
    result = Group(image, arrow, output_tex)
    result.arrange_submobjects(RIGHT)
    result.to_edge(UP)
    return result

def get_decimal_vector(nums, with_dots = True):
    decimals = VGroup()
    for num in nums:
        decimal = DecimalNumber(num)
        if num > 0:
            decimal.highlight(POSITIVE_COLOR)
        else:
            decimal.highlight(NEGATIVE_COLOR)
        decimals.add(decimal)
    contents = VGroup(*decimals)
    if with_dots:
        dots = TexMobject("\\vdots")
        contents.submobjects.insert(len(decimals)/2, dots)
    contents.arrange_submobjects(DOWN)
    lb, rb = brackets = TexMobject("\\big[", "\\big]")
    brackets.scale(2)
    brackets.stretch_to_fit_height(1.2*contents.get_height())
    lb.next_to(contents, LEFT, SMALL_BUFF)
    rb.next_to(contents, RIGHT, SMALL_BUFF)

    result = VGroup(lb, contents, brackets)
    result.lb = lb
    result.rb = rb
    result.brackets = brackets
    result.decimals = decimals
    result.contents = contents
    return result


########

class ShowLastVideo(TeacherStudentsScene):
    def construct(self):
        frame = ScreenRectangle()
        frame.scale_to_fit_height(4.5)
        frame.to_corner(UP+LEFT)
        title = TextMobject("But what \\emph{is} a Neural Network")
        title.move_to(frame)
        title.to_edge(UP)
        frame.next_to(title, DOWN)

        assumption_words = TextMobject(
            "I assume you've\\\\ watched this"
        )
        assumption_words.move_to(frame)
        assumption_words.to_edge(RIGHT)
        arrow = Arrow(RIGHT, LEFT, color = BLUE)
        arrow.next_to(assumption_words, LEFT)


        self.play(
            ShowCreation(frame),
            self.teacher.change, "raise_right_hand"
        )
        self.play(
            Write(title),
            self.get_student_changes(*["thinking"]*3)
        )
        self.play(
            Animation(title),
            GrowArrow(arrow),
            FadeIn(assumption_words)
        )
        self.dither(5)

class PreviewLearning(NetworkScene):
    CONFIG = {
        "layer_sizes" : DEFAULT_LAYER_SIZES,
        "network_mob_config" : {
            "neuron_to_neuron_buff" : SMALL_BUFF,
            "layer_to_layer_buff" : 2,
            "edge_stroke_width" : 1,
            "neuron_stroke_color" : WHITE,
            "neuron_stroke_width" : 2,
            "neuron_fill_color" : WHITE,
            "average_shown_activation_of_large_layer" : False,
            "edge_propogation_color" : GREEN,
            "edge_propogation_time" : 2,
            "include_output_labels" : True,
        },
        "n_examples" : 15,
        "max_stroke_width" : 3,
        "stroke_width_exp" : 3,
        "eta" : 3.0,
        "positive_edge_color" : BLUE,
        "negative_edge_color" : RED,
        "positive_change_color" : average_color(*2*[BLUE] + [YELLOW]),
        "negative_change_color" : average_color(*2*[RED] + [YELLOW]),
        "default_activate_run_time" : 1.5,
    }
    def construct(self):
        self.initialize_network()
        self.add_training_words()
        self.show_training()

    def initialize_network(self):
        self.network_mob.scale(0.7)
        self.network_mob.to_edge(DOWN)
        self.color_network_edges()

    def add_training_words(self):
        words = TextMobject("Training in \\\\ progress$\\dots$")
        words.scale(1.5)
        words.to_corner(UP+LEFT)

        self.add(words)

    def show_training(self):
        training_data, validation_data, test_data = load_data_wrapper()
        for train_in, train_out in training_data[:self.n_examples]:
            image = get_training_image_group(train_in, train_out)
            self.activate_network(train_in, FadeIn(image))
            self.backprop_one_example(
                train_in, train_out, 
                FadeOut(image), self.network_mob.layers.restore
            )

    def activate_network(self, train_in, *added_anims, **kwargs):
        network_mob = self.network_mob
        layers = network_mob.layers
        layers.save_state()
        activations = self.network.get_activation_of_all_layers(train_in)
        active_layers = [
            self.network_mob.get_active_layer(i, vect)
            for i, vect in enumerate(activations)
        ]
        all_edges = VGroup(*it.chain(*network_mob.edge_groups))
        run_time = kwargs.get("run_time", self.default_activate_run_time)
        edge_animation = LaggedStart(
            ShowCreationThenDestruction, 
            all_edges.copy().set_fill(YELLOW),
            run_time = run_time,
            lag_ratio = 0.3,
            remover = True,
        )
        layer_animation = Transform(
            VGroup(*layers), VGroup(*active_layers),
            run_time = run_time,
            submobject_mode = "lagged_start",
            rate_func = None,
        )

        self.play(edge_animation, layer_animation, *added_anims)

    def backprop_one_example(self, train_in, train_out, *added_outro_anims):
        network_mob = self.network_mob
        nabla_b, nabla_w = self.network.backprop(train_in, train_out)
        neuron_groups = VGroup(*[
            layer.neurons
            for layer in network_mob.layers[1:]
        ])
        delta_neuron_groups = neuron_groups.copy()
        edge_groups = network_mob.edge_groups
        delta_edge_groups = VGroup(*[
            edge_group.copy()
            for edge_group in edge_groups
        ])
        tups = zip(
            it.count(), nabla_b, nabla_w, 
            delta_neuron_groups, neuron_groups,
            delta_edge_groups, edge_groups
        )
        pc_color = self.positive_change_color
        nc_color = self.negative_change_color
        for i, nb, nw, delta_neurons, neurons, delta_edges, edges in reversed(tups):
            shown_nw = self.get_adjusted_first_matrix(nw)
            if np.max(shown_nw) == 0:
                shown_nw = (2*np.random.random(shown_nw.shape)-1)**5
            max_b = np.max(np.abs(nb))
            max_w = np.max(np.abs(shown_nw))
            for neuron, b in zip(delta_neurons, nb):
                color = nc_color if b > 0 else pc_color
                # neuron.set_fill(color, abs(b)/max_b)
                neuron.set_stroke(color, 3)
            for edge, w in zip(delta_edges.split(), shown_nw.T.flatten()):
                edge.set_stroke(
                    nc_color if w > 0 else pc_color,
                    3*abs(w)/max_w
                )
                edge.rotate_in_place(np.pi)
            if i == 2:
                delta_edges.submobjects = [
                    delta_edges[j]
                    for j in np.argsort(shown_nw.T.flatten())
                ]
            network = self.network
            network.weights[i] -= self.eta*nw
            network.biases[i] -= self.eta*nb

            self.play(
                ShowCreation(
                    delta_edges, submobject_mode = "all_at_once"
                ),
                FadeIn(delta_neurons),
                run_time = 0.5
            )
        edge_groups.save_state()
        self.color_network_edges()
        self.remove(edge_groups)
        self.play(*it.chain(
            [ReplacementTransform(
                edge_groups.saved_state, edge_groups,
            )],
            map(FadeOut, [delta_edge_groups, delta_neuron_groups]),
            added_outro_anims,
        ))

    #####

    def get_adjusted_first_matrix(self, matrix):
        n = self.network_mob.max_shown_neurons
        if matrix.shape[1] > n:
            half = matrix.shape[1]/2
            return matrix[:,half-n/2:half+n/2]
        else:
            return matrix

    def color_network_edges(self):
        layers = self.network_mob.layers
        weight_matrices = self.network.weights
        for layer, matrix in zip(layers[1:], weight_matrices):
            matrix = self.get_adjusted_first_matrix(matrix)
            matrix_max = np.max(matrix)
            for neuron, row in zip(layer.neurons, matrix):
                for edge, w in zip(neuron.edges_in, row):
                    if w > 0:
                        color = self.positive_edge_color
                    else:
                        color = self.negative_edge_color
                    msw = self.max_stroke_width
                    swe = self.stroke_width_exp
                    sw = msw*(abs(w)/matrix_max)**swe
                    sw = min(sw, msw)
                    edge.set_stroke(color, sw)

    def get_edge_animation(self):
        edges = VGroup(*it.chain(*self.network_mob.edge_groups))
        return LaggedStart(
            ApplyFunction, edges,
            lambda mob : (
                lambda m : m.rotate_in_place(np.pi/12).highlight(YELLOW),
                mob
            ),
            rate_func = wiggle
        )

class TrainingVsTestData(Scene):
    CONFIG = {
        "n_examples" : 10,
        "n_new_examples_shown" : 10,
    }
    def construct(self):
        self.initialize_data()
        self.introduce_all_data()
        self.subdivide_into_training_and_testing()
        self.scroll_through_much_data()

    def initialize_data(self):
        training_data, validation_data, test_data = load_data_wrapper()
        self.data = training_data
        self.curr_index = 0

    def get_examples(self):
        ci = self.curr_index
        self.curr_index += self.n_examples
        group = Group(*it.starmap(
            get_training_image_group,
            self.data[ci:ci+self.n_examples]
        ))
        group.arrange_submobjects(DOWN)
        group.scale(0.5)
        return group

    def introduce_all_data(self):
        training_examples, test_examples = [
            self.get_examples() for x in range(2)
        ]

        training_examples.next_to(ORIGIN, LEFT)
        test_examples.next_to(ORIGIN, RIGHT)
        self.play(
            LaggedStart(FadeIn, training_examples),
            LaggedStart(FadeIn, test_examples),
        )

        self.training_examples = training_examples
        self.test_examples = test_examples

    def subdivide_into_training_and_testing(self):
        training_examples = self.training_examples
        test_examples = self.test_examples
        for examples in training_examples, test_examples:
            examples.generate_target()
        training_examples.target.shift(2*LEFT)
        test_examples.target.shift(2*RIGHT)

        train_brace = Brace(training_examples.target, LEFT)
        train_words = train_brace.get_text("Train on \\\\ these")
        test_brace = Brace(test_examples.target, RIGHT)
        test_words = test_brace.get_text("Test on \\\\ these")

        bools = [True]*(len(test_examples)-1) + [False]
        random.shuffle(bools)
        marks = VGroup()
        for is_correct, test_example in zip(bools, test_examples.target):
            if is_correct:
                mark = TexMobject("\\checkmark")
                mark.highlight(GREEN)
            else:
                mark = TexMobject("\\times")
                mark.highlight(RED)
            mark.next_to(test_example, LEFT)
            marks.add(mark)

        self.play(
            MoveToTarget(training_examples),
            GrowFromCenter(train_brace),
            FadeIn(train_words)
        )
        self.dither()
        self.play(
            MoveToTarget(test_examples),
            GrowFromCenter(test_brace),
            FadeIn(test_words)
        )
        self.play(Write(marks))
        self.dither()

    def scroll_through_much_data(self):
        training_examples = self.training_examples
        colors = color_gradient([BLUE, YELLOW], self.n_new_examples_shown)
        for color in colors:
            new_examples = self.get_examples()
            new_examples.move_to(training_examples)
            for train_ex, new_ex in zip(training_examples, new_examples):
                self.remove(train_ex)
                self.add(new_ex)
                new_ex[0][0].highlight(color)
                self.dither(1./30)
            training_examples = new_examples

class NotSciFi(TeacherStudentsScene):
    def construct(self):
        students = self.students
        self.student_says(
            "Machines learning?!?",
            student_index = 0,
            target_mode = "pleading",
            run_time = 1,
        )
        bubble = students[0].bubble
        students[0].bubble = None
        self.student_says(
            "Should we \\\\ be worried?", student_index = 2,
            target_mode = "confused",
            bubble_kwargs = {"direction" : LEFT},
            run_time = 1,
        )
        self.dither()
        students[0].bubble = bubble
        self.teacher_says(
            "It's actually \\\\ just calculus.",
            run_time = 1
        )
        self.teacher.bubble = None
        self.dither()
        self.student_says(
            "Even worse!", 
            target_mode = "horrified",
            bubble_kwargs = {
                "direction" : LEFT, 
                "width" : 3,
                "height" : 2,
            },
        )
        self.dither(2)

class FunctionMinmization(GraphScene):
    CONFIG = {
        "x_labeled_nums" : range(-1, 10),
    }
    def construct(self):
        self.setup_axes()
        title = TextMobject("Finding minima")
        title.to_edge(UP)
        self.add(title)

        def func(x):
            x -= 4.5
            return 0.03*(x**4 - 16*x**2) + 0.3*x + 4
        graph = self.get_graph(func)
        graph_label = self.get_graph_label(graph, "C(x)")
        self.add(graph, graph_label)

        dots = VGroup(*[
            Dot().move_to(self.input_to_graph_point(x, graph))
            for x in range(10)
        ])
        dots.gradient_highlight(YELLOW, RED)

        def update_dot(dot, dt):
            x = self.x_axis.point_to_number(dot.get_center())
            slope = self.slope_of_tangent(x, graph)
            x -= slope*dt
            dot.move_to(self.input_to_graph_point(x, graph))

        self.add(*[
            ContinualUpdateFromFunc(dot, update_dot)
            for dot in dots
        ])
        self.dither(10)

class IntroduceCostFunction(PreviewLearning):
    CONFIG = {
        "max_stroke_width" : 2,
        "full_edges_exp" : 5,
        "n_training_examples" : 100,
        "bias_color" : MAROON_B
    }
    def construct(self):
        self.network_mob.shift(LEFT)
        self.isolate_one_neuron()
        self.reminder_of_weights_and_bias()
        self.bring_back_rest_of_network()
        self.feed_in_example()
        self.make_fun_of_output()
        self.need_a_cost_function()
        self.fade_all_but_last_layer()
        self.break_down_cost_function()
        self.average_over_all_training_data()

    def isolate_one_neuron(self):
        network_mob = self.network_mob
        neurons = VGroup(*it.chain(*[
            layer.neurons
            for layer in network_mob.layers[1:]
        ]))
        edges = VGroup(*it.chain(*network_mob.edge_groups))
        neuron = network_mob.layers[1].neurons[7]
        neurons.remove(neuron)
        edges.remove(*neuron.edges_in)
        output_labels = network_mob.output_labels
        kwargs = {
            "submobject_mode" : "lagged_start",
            "run_time" : 2,
        }
        self.play(
            FadeOut(edges, **kwargs),
            FadeOut(neurons, **kwargs),
            FadeOut(output_labels, **kwargs),
            Animation(neuron),
            neuron.edges_in.set_stroke, None, 2,
        )

        self.neuron = neuron

    def reminder_of_weights_and_bias(self):
        neuron = self.neuron
        layer0 = self.network_mob.layers[0]
        active_layer0 = self.network_mob.get_active_layer(
            0, np.random.random(len(layer0.neurons))
        )
        prev_neurons = layer0.neurons

        weighted_edges = VGroup(*[
            self.color_edge_randomly(edge.copy(), exp = 1)
            for edge in neuron.edges_in
        ])

        formula = TexMobject(
            "=", "\\sigma(",
            "w_1", "a_1", "+",
            "w_2", "a_2", "+",
            "\\cdots", "+",
            "w_n", "a_n", "+", "b", ")"
        )
        w_labels = formula.get_parts_by_tex("w_")
        a_labels = formula.get_parts_by_tex("a_")
        b = formula.get_part_by_tex("b")
        sigma = VGroup(
            formula.get_part_by_tex("\\sigma"),
            formula.get_part_by_tex(")"),
        )
        symbols = VGroup(*[
            formula.get_parts_by_tex(tex)
            for tex in "=", "+", "dots"
        ])

        w_labels.highlight(self.positive_edge_color)
        b.highlight(self.bias_color)
        sigma.highlight(YELLOW)
        formula.next_to(neuron, RIGHT)

        weights_word = TextMobject("Weights")
        weights_word.next_to(neuron.edges_in, RIGHT, aligned_edge = UP)
        weights_word.highlight(self.positive_edge_color)
        weights_arrow_to_edges = Arrow(
            weights_word.get_bottom(),
            neuron.edges_in[0].get_center(),
            color = self.positive_edge_color
        )

        weights_arrow_to_syms = VGroup(*[
            Arrow(
                weights_word.get_bottom(),
                w_label.get_top(),
                color = self.positive_edge_color
            )
            for w_label in w_labels
        ])

        bias_word = TextMobject("Bias")
        bias_arrow = Vector(DOWN, color = self.bias_color)
        bias_arrow.next_to(b, UP, SMALL_BUFF)
        bias_word.next_to(bias_arrow, UP, SMALL_BUFF)
        bias_word.highlight(self.bias_color)

        self.play(
            Transform(layer0, active_layer0),
            neuron.set_fill, None, 0.5,
            FadeIn(formula),
            run_time = 2,
            submobject_mode = "lagged_start"
        )
        self.play(LaggedStart(
            ShowCreationThenDestruction, 
            neuron.edges_in.copy().set_stroke(YELLOW, 3),
            run_time = 1.5,
            lag_ratio = 0.7,
            remover = True
        ))
        self.play(
            Write(weights_word),
            *map(GrowArrow, weights_arrow_to_syms),
            run_time = 1
        )
        self.dither()
        self.play(
            ReplacementTransform(
                w_labels.copy(), weighted_edges,
                remover = True
            ),
            Transform(neuron.edges_in, weighted_edges),
            ReplacementTransform(
                weights_arrow_to_syms,
                VGroup(weights_arrow_to_edges),
            )
        )
        self.dither()
        self.play(
            Write(bias_word),
            GrowArrow(bias_arrow),
            run_time = 1
        )
        self.dither(2)

        ## Initialize randomly
        w_random = TextMobject("Initialize randomly")
        w_random.move_to(weights_word, LEFT)
        b_random = w_random.copy()
        b_random.move_to(bias_word, RIGHT)

        self.play(
            Transform(weights_word, w_random),
            Transform(bias_word, b_random),
            *[
                ApplyFunction(self.color_edge_randomly, edge)
                for edge in neuron.edges_in
            ]
        )
        self.play(LaggedStart(
            ApplyMethod, neuron.edges_in,
            lambda m : (m.rotate_in_place, np.pi/12),
            rate_func = wiggle,
            run_time = 2
        ))
        self.play(*map(FadeOut, [
            weights_word, weights_arrow_to_edges,
            bias_word, bias_arrow,
            formula
        ]))

    def bring_back_rest_of_network(self):
        network_mob = self.network_mob
        neurons = VGroup(*network_mob.layers[1].neurons)
        neurons.remove(self.neuron)
        for layer in network_mob.layers[2:]:
            neurons.add(*layer.neurons)
        neurons.add(*network_mob.output_labels)

        edges = VGroup(*network_mob.edge_groups[0])
        edges.remove(*self.neuron.edges_in)
        for edge_group in network_mob.edge_groups[1:]:
            edges.add(*edge_group)

        for edge in edges:
            self.color_edge_randomly(edge, exp = self.full_edges_exp)

        self.play(*[
            LaggedStart(
                FadeIn, group,
                run_time = 3,
            )
            for group in neurons, edges
        ])

    def feed_in_example(self):
        vect = get_organized_images()[3][5]
        image = PixelsFromVect(vect)
        image.to_corner(UP+LEFT)
        rect = SurroundingRectangle(image, color = BLUE)
        neurons = VGroup(*[
            Circle(
                stroke_width = 1,
                stroke_color = WHITE,
                fill_opacity = pixel.fill_rgb[0],
                fill_color = WHITE,
                radius = pixel.get_height()/2
            ).move_to(pixel)
            for pixel in image
        ])
        layer0= self.network_mob.layers[0]
        n = self.network_mob.max_shown_neurons
        neurons.target = VGroup(*it.chain(
            VGroup(*layer0.neurons[:n/2]).set_fill(opacity = 0),
            [
                VectorizedPoint(layer0.dots.get_center())
                for x in xrange(len(neurons)-n)
            ],
            VGroup(*layer0.neurons[-n/2:]).set_fill(opacity = 0),
        ))

        self.play(
            self.network_mob.shift, 0.5*RIGHT,
            ShowCreation(rect),
            LaggedStart(DrawBorderThenFill, image),
            LaggedStart(DrawBorderThenFill, neurons),
            run_time = 1
        )
        self.play(
            MoveToTarget(
                neurons, submobject_mode = "lagged_start",
                remover = True
            ),
            layer0.neurons.set_fill, None, 0,
        )
        self.activate_network(vect, run_time = 2)

        self.image = image
        self.image_rect = rect

    def make_fun_of_output(self):
        last_layer = self.network_mob.layers[-1].neurons
        last_layer.add(self.network_mob.output_labels)
        rect = SurroundingRectangle(last_layer)
        words = TextMobject("Utter trash")
        words.next_to(rect, DOWN, aligned_edge = LEFT)
        VGroup(rect, words).highlight(YELLOW)

        self.play(
            ShowCreation(rect),
            Write(words, run_time = 2)
        )
        self.dither()

        self.trash_rect = rect
        self.trash_words = words

    def need_a_cost_function(self):
        vect = np.zeros(10)
        vect[3] = 1
        output_labels = self.network_mob.output_labels
        desired_layer = self.network_mob.get_active_layer(-1, vect)
        layer = self.network_mob.layers[-1]
        layer.add(output_labels)
        desired_layer.add(output_labels.copy())
        desired_layer.shift(2*RIGHT)
        layers = VGroup(layer, desired_layer)

        words = TextMobject(
            "What's the", "``cost''\\\\", "of this difference?",
        )
        words.highlight_by_tex("cost", RED)
        words.next_to(layers, UP)
        words.to_edge(UP)
        words.shift_onto_screen()
        double_arrow = DoubleArrow(
            layer.get_right(),
            desired_layer.get_left(),
            color = RED
        )

        self.play(FadeIn(words))
        self.play(ReplacementTransform(layer.copy(), desired_layer))
        self.play(GrowFromCenter(double_arrow))
        self.dither(2)

        self.desired_last_layer = desired_layer
        self.diff_arrow = double_arrow

    def fade_all_but_last_layer(self):
        network_mob = self.network_mob
        to_fade = VGroup(*it.chain(*zip(
            network_mob.layers[:-1],
            network_mob.edge_groups
        )))

        self.play(LaggedStart(FadeOut, to_fade, run_time = 1))

    def break_down_cost_function(self):
        layer = self.network_mob.layers[-1]
        desired_layer = self.desired_last_layer
        decimal_groups = VGroup(*[
            self.num_vect_to_decimals(self.layer_to_num_vect(l))
            for l in layer, desired_layer
        ])

        terms = VGroup()
        symbols = VGroup()
        for d1, d2 in zip(*decimal_groups):
            term = TexMobject(
                "(", "0.00", "-", "0.00", ")^2", "+",
            )
            term.scale(d1.get_height()/term[1].get_height())
            for d, i in (d1, 1), (d2, 3):
                term.submobjects[i] = d.move_to(term[i])
            terms.add(term)
            symbols.add(*term)
            symbols.remove(d1, d2)
            last_plus = term[-1]
        for mob in terms[-1], symbols:
            mob.remove(last_plus)
        terms.arrange_submobjects(
            DOWN, buff = SMALL_BUFF,
            aligned_edge = LEFT
        )
        terms.scale_to_fit_height(1.5*layer.get_height())
        terms.next_to(layer, LEFT, buff = 2)

        image_group = Group(self.image, self.image_rect)
        image_group.generate_target()
        image_group.target.scale(0.5)
        cost_of = TextMobject("Cost of").highlight(RED)
        cost_group = VGroup(cost_of, image_group.target)
        cost_group.arrange_submobjects(RIGHT)
        brace = Brace(terms, LEFT)
        cost_group.next_to(brace, LEFT)

        self.revert_to_original_skipping_status()
        self.play(*[
            ReplacementTransform(
                VGroup(*l.neurons[:10]).copy(), dg
            )
            for l, dg in zip([layer, desired_layer], decimal_groups)
        ])
        self.play(
            FadeIn(symbols),
            MoveToTarget(image_group),
            FadeIn(cost_of),
            GrowFromCenter(brace),
        )
        self.dither()

        self.decimal_groups = decimal_groups
        self.image_group = image_group
        self.cost_group = VGroup(cost_of, image_group)

    def average_over_all_training_data(self):
        image_group = self.image_group
        decimal_groups = self.decimal_groups

        random_neurons = self.network_mob.layers[-1].neurons
        desired_neurons = self.desired_last_layer.neurons

        dither_times = iter(it.chain(
            4*[0.5],
            4*[0.25],
            8*[0.125],
            it.repeat(0.1)
        ))

        words = TextMobject("Average cost of \\\\ all training data...")
        words.highlight(BLUE)
        words.to_corner(UP+LEFT)

        self.play(
            Write(words, run_time = 1),
        )

        training_data, validation_data, test_data = load_data_wrapper()
        for in_vect, out_vect in training_data[:self.n_training_examples]:
            random_v = np.random.random(10)
            new_decimal_groups = VGroup(*[
                self.num_vect_to_decimals(v)
                for v in random_v, out_vect
            ])
            for ds, nds in zip(decimal_groups, new_decimal_groups):
                for old_d, new_d in zip(ds, nds):
                    new_d.replace(old_d)
            self.remove(decimal_groups)
            self.add(new_decimal_groups)
            decimal_groups = new_decimal_groups
            for pair in (random_v, random_neurons), (out_vect, desired_neurons):
                for n, neuron in zip(*pair):
                    neuron.set_fill(opacity = n)
            new_image_group = MNistMobject(in_vect)
            new_image_group.replace(image_group)
            self.remove(image_group)
            self.add(new_image_group)
            image_group = new_image_group

            self.dither(dither_times.next())

    ####

    def color_edge_randomly(self, edge, exp = 1):
        r = (2*np.random.random()-1)**exp
        r *= self.max_stroke_width
        pc, nc = self.positive_edge_color, self.negative_edge_color
        edge.set_stroke(
            color = pc if r > 0 else nc,
            width = abs(r),
        )
        return edge

    def layer_to_num_vect(self, layer, n_terms = 10):
        return [
            n.get_fill_opacity()
            for n in layer.neurons
        ][:n_terms]

    def num_vect_to_decimals(self, num_vect):
        return VGroup(*[
            DecimalNumber(n).set_fill(opacity = 0.5*n + 0.5)
            for n in num_vect
        ])

    def num_vect_to_column_vector(self, num_vect, height):
        decimals = VGroup(*[
            DecimalNumber(n).set_fill(opacity = 0.5*n + 0.5)
            for n in num_vect
        ])
        decimals.arrange_submobjects(DOWN)
        decimals.scale_to_fit_height(height)
        lb, rb = brackets = TexMobject("[]")
        brackets.scale(2)
        brackets.stretch_to_fit_height(height + SMALL_BUFF)
        lb.next_to(decimals, LEFT)
        rb.next_to(decimals, RIGHT)
        result = VGroup(brackets, decimals)
        result.brackets = brackets
        result.decimals = decimals
        return result

class ThisIsVeryComplicated(TeacherStudentsScene):
    def construct(self):
        self.teacher_says(
            "Very complicated!",
            target_mode = "surprised",
            run_time = 1,
        )
        self.change_student_modes(*3*["guilty"])
        self.dither(2)

class EmphasizeComplexityOfCostFunction(IntroduceCostFunction):
    CONFIG = {
        "stroke_width_exp" : 3,
        "n_examples" : 32,
    }
    def construct(self):
        self.setup_sides()
        self.show_network_as_a_function()
        self.show_cost_function()

    def setup_sides(self):
        v_line = Line(UP, DOWN).scale(SPACE_HEIGHT)
        network_mob = self.network_mob
        network_mob.scale_to_fit_width(SPACE_WIDTH - 1)
        network_mob.to_corner(DOWN+LEFT)

        self.add(v_line)
        self.color_network_edges()

    def show_network_as_a_function(self):
        title = TextMobject("Neural network function")
        title.shift(SPACE_WIDTH*RIGHT/2)
        title.to_edge(UP)
        underline = Line(LEFT, RIGHT)
        underline.stretch_to_fit_width(title.get_width())
        underline.next_to(title, DOWN, SMALL_BUFF)
        self.add(title, underline)

        words = self.get_function_description_words(
            "784 numbers (pixels)",
            "10 numbers",
            "13{,}002 weights/biases",
        )
        input_words, output_words, parameter_words = words
        for word in words:
            self.add(word[0])

        in_vect = get_organized_images()[7][8]
        activations = self.network.get_activation_of_all_layers(in_vect)
        image = MNistMobject(in_vect)
        image.scale_to_fit_height(1.5)
        image_label = TextMobject("Input")
        image_label.highlight(input_words[0].get_color())
        image_label.next_to(image, UP, SMALL_BUFF)

        arrow = Arrow(LEFT, RIGHT, color = WHITE)
        arrow.next_to(image, RIGHT)
        output = self.num_vect_to_column_vector(activations[-1], 2)
        output.next_to(arrow, RIGHT)

        group = Group(image, image_label, arrow, output)
        group.next_to(self.network_mob, UP, 0, RIGHT)

        dot = Dot()
        dot.move_to(input_words.get_right())
        dot.set_fill(opacity = 0.5)

        self.play(FadeIn(input_words[1], submobject_mode = "lagged_start"))
        self.play(
            dot.move_to, image,
            dot.set_fill, None, 0,
            FadeIn(image),
            FadeIn(image_label),
        )
        self.activate_network(in_vect, 
            GrowArrow(arrow),
            FadeIn(output),
            FadeIn(output_words[1])
        )
        self.dither()
        self.play(
            FadeIn(parameter_words[1]), 
            self.get_edge_animation()
        )
        self.dither(2)

        self.to_fade = group
        self.curr_words = words
        self.title = title
        self.underline = underline

    def show_cost_function(self):
        network_mob = self.network_mob
        to_fade = self.to_fade
        input_words, output_words, parameter_words = self.curr_words

        network_mob.generate_target()
        network_mob.target.scale_in_place(0.7)
        network_mob.target.to_edge(UP, buff = LARGE_BUFF)
        rect = SurroundingRectangle(network_mob.target, color = BLUE)
        network_label = TextMobject("Input")
        network_label.highlight(input_words[0].get_color())
        network_label.next_to(rect, UP, SMALL_BUFF)

        new_output_word = TextMobject("1 number", "(the cost)")
        new_output_word[1].highlight(RED).scale(0.9)
        new_output_word.move_to(output_words[1], LEFT)
        new_output_word.shift(0.5*SMALL_BUFF*DOWN)
        new_parameter_word = TextMobject("""
            \\begin{flushleft}
            Many, many, many \\\\ training examples
            \\end{flushleft}
        """).scale(0.9)
        new_parameter_word.move_to(parameter_words[1], UP+LEFT) 

        new_title = TextMobject("Cost function")
        new_title.highlight(RED)
        new_title.move_to(self.title)

        arrow = Arrow(UP, DOWN, color = WHITE)
        arrow.next_to(rect, DOWN)
        cost = TextMobject("Cost: 5.4")
        cost.highlight(RED)
        cost.next_to(arrow, DOWN)

        training_data, validation_data, test_data = load_data_wrapper()
        training_examples = Group(*map(
            self.get_training_pair_mob, 
            training_data[:self.n_examples]
        ))
        training_examples.next_to(parameter_words, DOWN, buff = LARGE_BUFF)

        self.play(
            FadeOut(to_fade),
            FadeOut(input_words[1]),
            FadeOut(output_words[1]),
            MoveToTarget(network_mob),
            FadeIn(rect),
            FadeIn(network_label),
            Transform(self.title, new_title),
            self.underline.stretch_to_fit_width, new_title.get_width()
        )
        self.play(
            ApplyMethod(
                parameter_words[1].move_to, input_words[1], LEFT,
                path_arc = np.pi,
            ),
            self.get_edge_animation()
        )
        self.dither()
        self.play(
            GrowArrow(arrow),
            Write(cost, run_time = 1)
        )
        self.play(Write(new_output_word, run_time = 1))
        self.dither()
        self.play(
            FadeIn(new_parameter_word),
            FadeIn(training_examples[0])
        )
        self.dither(0.5)
        for last_ex, ex in zip(training_examples, training_examples[1:]):
            activations = self.network.get_activation_of_all_layers(
                ex.in_vect
            )
            for i, a in enumerate(activations):
                layer = self.network_mob.layers[i]
                active_layer = self.network_mob.get_active_layer(i, a)
                Transform(layer, active_layer).update(1)
            self.remove(last_ex)
            self.add(ex)
            self.dither(0.25)

    ####

    def get_function_description_words(self, w1, w2, w3):
        input_words = TextMobject("Input:", w1)
        input_words[0].highlight(BLUE)
        output_words = TextMobject("Output:", w2)
        output_words[0].highlight(YELLOW)
        parameter_words = TextMobject("Parameters:", w3)
        parameter_words[0].highlight(GREEN)
        words = VGroup(input_words, output_words, parameter_words)
        words.arrange_submobjects(DOWN, aligned_edge = LEFT)
        words.scale(0.9)
        words.next_to(ORIGIN, RIGHT)
        words.shift(UP)
        return words

    def get_training_pair_mob(self, data):
        in_vect, out_vect = data
        image = MNistMobject(in_vect)
        image.scale_to_fit_height(1)
        comma = TextMobject(",")
        comma.next_to(image, RIGHT, SMALL_BUFF, DOWN)
        output = TexMobject(str(np.argmax(out_vect)))
        output.scale_to_fit_height(0.75)
        output.next_to(image, RIGHT, MED_SMALL_BUFF)
        lp, rp = parens = TextMobject("()")
        parens.scale(2)
        parens.stretch_to_fit_height(1.2*image.get_height())
        lp.next_to(image, LEFT, SMALL_BUFF)
        rp.next_to(lp, RIGHT, buff = 2)

        result = Group(lp, image, comma, output, rp)
        result.in_vect = in_vect
        return result

class YellAtNetwork(PiCreatureScene, PreviewLearning):
    def setup(self):
        PiCreatureScene.setup(self)
        PreviewLearning.setup(self)

    def construct(self):
        randy = self.randy

        network_mob = self.network_mob
        network_mob.scale(0.5)
        network_mob.next_to(randy, RIGHT, LARGE_BUFF)
        self.color_network_edges()
        eyes = Eyes(network_mob.edge_groups[1])

        self.play(
            PiCreatureBubbleIntroduction(
                randy, "Horrible!",
                target_mode = "angry", 
                look_at_arg = eyes,
                run_time = 1,
            ),
            eyes.look_at_anim(randy.eyes)
        )
        self.play(eyes.change_mode_anim("sad"))
        self.play(eyes.look_at_anim(3*DOWN + 3*RIGHT))
        self.dither()
        self.play(eyes.blink_anim())
        self.dither()

    ####

    def create_pi_creature(self):
        randy = self.randy = Randolph()
        randy.shift(3*LEFT + DOWN)
        return randy

class SingleVariableCostFunction(GraphScene):
    CONFIG = {
        "x_axis_label" : "$w$",
        "y_axis_label" : "",
        "x_min" : -5,
        "x_max" : 7,
        "x_axis_width" : 12,
        "graph_origin" : 2.5*DOWN + LEFT,
        "tangent_line_color" : YELLOW,
    }
    def construct(self):
        self.reduce_full_function_to_single_variable()
        self.show_graph()
        self.find_exact_solution()
        self.make_function_more_complicated()
        self.take_steps()
        self.take_steps_based_on_slope()
        self.ball_rolling_down_hill()
        self.note_step_sizes()

    def reduce_full_function_to_single_variable(self):
        name = TextMobject("Cost function")
        cf1 = TexMobject("C(", "w_1, w_2, \\dots, w_{13{,}002}", ")")
        cf2 = TexMobject("C(", "w", ")")
        for cf in cf1, cf2:
            VGroup(cf[0], cf[2]).highlight(RED)
        big_brace, lil_brace = [
            Brace(cf[1], DOWN)
            for cf in cf1, cf2
        ]
        big_brace_text = big_brace.get_text("Weights and biases")
        lil_brace_text = lil_brace.get_text("Single input")

        name.next_to(cf1, UP, LARGE_BUFF)
        name.highlight(RED)

        self.add(name, cf1)
        self.play(
            GrowFromCenter(big_brace),
            FadeIn(big_brace_text)
        )
        self.dither()
        self.play(
            ReplacementTransform(big_brace, lil_brace),
            ReplacementTransform(big_brace_text, lil_brace_text),
            ReplacementTransform(cf1, cf2),
        )

        # cf2.add_background_rectangle()
        lil_brace_text.add_background_rectangle()
        self.brace_group = VGroup(lil_brace, lil_brace_text)
        cf2.add(self.brace_group)
        self.function_label = cf2
        self.to_fade = name

    def show_graph(self):
        function_label = self.function_label
        self.setup_axes()
        graph = self.get_graph(
            lambda x : 0.5*(x - 3)**2 + 2,
            color = RED
        )

        self.play(
            FadeOut(self.to_fade),
            Write(self.axes),
            Animation(function_label),
            run_time = 1,
        )
        self.play(
            function_label.next_to, 
                self.input_to_graph_point(5, graph), RIGHT,
            ShowCreation(graph)
        )
        self.dither()

        self.graph = graph

    def find_exact_solution(self):
        function_label = self.function_label
        graph = self.graph

        w_min = TexMobject("w", "_{\\text{min}}", arg_separator = "")
        w_min.move_to(function_label[1], UP+LEFT)
        w_min[1].fade(1)
        x = 3
        dot = Dot(
            self.input_to_graph_point(x, graph),
            color = YELLOW
        )
        line = self.get_vertical_line_to_graph(
            x, graph, 
            line_class = DashedLine,
            color = YELLOW
        )
        formula = TexMobject("\\frac{dC}{dw}(w) = 0")
        formula.next_to(dot, UP, buff = 2)
        formula.shift(LEFT)
        arrow = Arrow(formula.get_bottom(), dot.get_center())

        self.play(
            w_min.shift, 
                line.get_bottom() - w_min[0].get_top(),
                MED_SMALL_BUFF*DOWN,
            w_min.set_fill, WHITE, 1,
        )
        self.play(ShowCreation(line))
        self.play(DrawBorderThenFill(dot, run_time = 1))
        self.dither()
        self.play(Write(formula, run_time = 2))
        self.play(GrowArrow(arrow))
        self.dither()

        self.dot = dot
        self.line = line
        self.w_min = w_min
        self.deriv_group = VGroup(formula, arrow)

    def make_function_more_complicated(self):
        dot = self.dot
        line = self.line
        w_min = self.w_min
        deriv_group = self.deriv_group
        function_label = self.function_label
        brace_group = function_label[-1]
        function_label.remove(brace_group)

        brace = Brace(deriv_group, UP)
        words = TextMobject("Sometimes \\\\ infeasible")
        words.next_to(deriv_group, UP)
        words.highlight(BLUE)
        words.next_to(brace, UP)

        graph = self.get_graph(
            lambda x : 0.05*((x+2)*(x-1)*(x-3))**2 + 2 + 0.3*(x-3),
            color = RED
        )

        self.play(
            ReplacementTransform(self.graph, graph),
            function_label.shift, 2*UP+1.9*LEFT,
            FadeOut(brace_group),
            Animation(dot)
        )
        self.graph = graph
        self.play(
            Write(words, run_time = 1),
            GrowFromCenter(brace)
        )
        self.dither(2)
        self.play(FadeOut(VGroup(words, brace, deriv_group)))

    def take_steps(self):
        dot = self.dot
        line = self.line
        w_mob, min_mob = self.w_min
        graph = self.graph

        def update_line(line):
            x = self.x_axis.point_to_number(w_mob.get_center())
            line.put_start_and_end_on_with_projection(
                self.coords_to_point(x, 0),
                self.input_to_graph_point(x, graph)
            )
            return line
        line_update_anim = UpdateFromFunc(line, update_line)

        def update_dot(dot):
            dot.move_to(line.get_end())
            return dot
        dot_update_anim = UpdateFromFunc(dot, update_dot)

        point = self.coords_to_point(2, 0)
        arrows = VGroup()
        q_marks = VGroup()
        for vect, color in (LEFT, BLUE), (RIGHT, GREEN):
            arrow = Arrow(ORIGIN, vect, buff = SMALL_BUFF)
            arrow.shift(point + SMALL_BUFF*UP)
            arrow.highlight(color)
            arrows.add(arrow)
            q_mark = TextMobject("?")
            q_mark.next_to(arrow, UP, buff = 0)
            q_mark.add_background_rectangle()
            q_marks.add(q_mark)

        self.play(
            w_mob.next_to, point, DOWN,
            FadeOut(min_mob),
            line_update_anim, 
            dot_update_anim,
        )
        self.dither()
        self.play(*it.chain(
            map(GrowArrow, arrows),
            map(FadeIn, q_marks),
        ))
        self.dither()

        self.arrow_group = VGroup(arrows, q_marks)
        self.line_update_anim = line_update_anim
        self.dot_update_anim = dot_update_anim
        self.w_mob = w_mob

    def take_steps_based_on_slope(self):
        arrows, q_marks = arrow_group = self.arrow_group
        line_update_anim = self.line_update_anim
        dot_update_anim = self.dot_update_anim
        dot = self.dot
        w_mob = self.w_mob
        graph = self.graph

        x = self.x_axis.point_to_number(w_mob.get_center())
        tangent_line = self.get_tangent_line(x, arrows[0].get_color())

        self.play(
            ShowCreation(tangent_line),
            Animation(dot),
        )
        self.play(VGroup(arrows[1], q_marks).set_fill, None, 0)
        self.play(
            w_mob.shift, MED_SMALL_BUFF*LEFT,
            MaintainPositionRelativeTo(arrow_group, w_mob),
            line_update_anim, dot_update_anim,
        )
        self.dither()

        new_x = 0.3
        new_point = self.coords_to_point(new_x, 0)
        new_tangent_line = self.get_tangent_line(
            new_x, arrows[1].get_color()
        )
        self.play(
            FadeOut(tangent_line),
            w_mob.next_to, new_point, DOWN,
            arrow_group.next_to, new_point, UP, SMALL_BUFF,
            arrow_group.set_fill, None, 1,
            dot_update_anim,
            line_update_anim,
        )
        self.play(
            ShowCreation(new_tangent_line),
            Animation(dot),
            Animation(arrow_group),
        )
        self.dither()
        self.play(VGroup(arrows[0], q_marks).set_fill, None, 0)
        self.play(
            w_mob.shift, MED_SMALL_BUFF*RIGHT,
            MaintainPositionRelativeTo(arrow_group, w_mob),
            line_update_anim, dot_update_anim,
        )
        self.play(
            FadeOut(VGroup(new_tangent_line, arrow_group)),
            Animation(dot),
        )
        self.dither()
        for x in 0.8, 1.1, 0.95:
            self.play(
                w_mob.next_to, self.coords_to_point(x, 0), DOWN,
                line_update_anim,
                dot_update_anim,
            )
        self.dither()

    def ball_rolling_down_hill(self):
        ball = self.dot
        graph = self.graph
        point = VectorizedPoint(self.coords_to_point(-0.5, 0))
        w_mob = self.w_mob

        def update_ball(ball):
            x = self.x_axis.point_to_number(ball.point.get_center())
            graph_point = self.input_to_graph_point(x, graph)
            vect = rotate_vector(UP, self.angle_of_tangent(x, graph))
            radius = ball.get_width()/2
            ball.move_to(graph_point + radius*vect)
            return ball

        def update_point(point, dt):
            x = self.x_axis.point_to_number(point.get_center())
            slope = self.slope_of_tangent(x, graph)
            if abs(slope) > 0.5:
                slope = 0.5 * slope / abs(slope)
            x -= slope*dt
            point.move_to(self.coords_to_point(x, 0))


        ball.generate_target()
        ball.target.scale(2)
        ball.target.set_fill(opacity = 0)
        ball.target.set_stroke(BLUE, 3)
        ball.point = point
        ball.target.point = point
        update_ball(ball.target)

        self.play(MoveToTarget(ball))
        self.play(
            point.move_to, w_mob,
            UpdateFromFunc(ball, update_ball),
            run_time = 3,
        )
        self.dither(2)

        points = [
            VectorizedPoint(self.coords_to_point(x, 0))
            for x in np.linspace(-2.7, 3.7, 11)
        ]
        balls = VGroup()
        updates = []
        for point in points:
            new_ball = ball.copy() 
            new_ball.point = point
            balls.add(new_ball)
            updates += [
                ContinualUpdateFromFunc(point, update_point),
                ContinualUpdateFromFunc(new_ball, update_ball)
            ]
        balls.gradient_highlight(BLUE, GREEN)

        self.play(ReplacementTransform(ball, balls))
        self.add(*updates)
        self.dither(5)
        self.remove(*updates)
        self.remove(*points)
        self.play(FadeOut(balls))

    def note_step_sizes(self):
        w_mob = self.w_mob
        line_update_anim = self.line_update_anim

        x = -0.5
        target_x = 0.94
        point = VectorizedPoint(self.coords_to_point(x, 0))
        line = self.get_tangent_line(x)
        line.scale_in_place(0.5)
        def update_line(line):
            x = self.x_axis.point_to_number(point.get_center())
            self.make_line_tangent(line, x)
            return line

        self.play(
            ShowCreation(line),
            w_mob.next_to, point, DOWN,
            line_update_anim,
        )
        for n in range(6):
            x = self.x_axis.point_to_number(point.get_center())
            new_x = interpolate(x, target_x, 0.5)
            self.play(
                point.move_to, self.coords_to_point(new_x, 0),
                MaintainPositionRelativeTo(w_mob, point),
                line_update_anim,
                UpdateFromFunc(line, update_line),
            )
            self.dither(0.5)
        self.dither()

    ###

    def get_tangent_line(self, x, color = YELLOW):
        tangent_line = Line(LEFT, RIGHT).scale(3)
        tangent_line.highlight(color)
        self.make_line_tangent(tangent_line, x)
        return tangent_line

    def make_line_tangent(self, line, x):
        graph = self.graph
        line.rotate(self.angle_of_tangent(x, graph) - line.get_angle())
        line.move_to(self.input_to_graph_point(x, graph))

class TwoVariableInputSpace(Scene):
    def construct(self):
        self.add_plane()
        self.ask_about_direction()
        self.show_gradient()

    def add_plane(self):
        plane = NumberPlane(
            x_radius = SPACE_WIDTH/2
        )
        plane.add_coordinates()
        name = TextMobject("Input space")
        name.add_background_rectangle()
        name.next_to(plane.get_corner(UP+LEFT), DOWN+RIGHT)
        x, y = map(TexMobject, ["x", "y"])
        x.next_to(plane.coords_to_point(3.25, 0), UP, SMALL_BUFF)
        y.next_to(plane.coords_to_point(0, 3.6), RIGHT, SMALL_BUFF)

        self.play(
            *map(Write, [plane, name, x, y]),
            run_time = 1
        )
        self.dither()

        self.plane = plane

    def ask_about_direction(self):
        point = self.plane.coords_to_point(2, 1)
        dot = Dot(point, color = YELLOW)
        dot.save_state()
        dot.move_to(SPACE_HEIGHT*UP + SPACE_WIDTH*RIGHT/2)
        dot.fade(1)
        arrows = VGroup(*[
            Arrow(ORIGIN, vect).shift(point)
            for vect in compass_directions(8)
        ])
        arrows.highlight(WHITE)
        question = TextMobject(
            "Which direction decreases \\\\",
            "$C(x, y)$", "most quickly?"
        )
        question.scale(0.7)
        question.highlight(YELLOW)
        question.highlight_by_tex("C(x, y)", RED)
        question.add_background_rectangle()
        question.next_to(arrows, LEFT)

        self.play(dot.restore)
        self.play(
            FadeIn(question),
            LaggedStart(GrowArrow, arrows)
        )
        self.dither()

        self.arrows = arrows
        self.dot = dot
        self.question = question

    def show_gradient(self):
        arrows = self.arrows
        dot = self.dot
        question = self.question

        arrow = arrows[3]
        new_arrow = Arrow(
            dot.get_center(), arrow.get_end(),
            buff = 0,
            color = GREEN
        )
        new_arrow.highlight(GREEN)
        arrow.save_state()

        gradient = TexMobject("\\nabla C(x, y)")
        gradient.add_background_rectangle()
        gradient.next_to(arrow.get_end(), UP, SMALL_BUFF)

        gradient_words = TextMobject(
            "``Gradient'', the direction\\\\ of",
            "steepest increase"
        )
        gradient_words.scale(0.7)
        gradient_words[-1].highlight(GREEN)
        gradient_words.next_to(gradient, UP, SMALL_BUFF)
        gradient_words.add_background_rectangle(opacity = 1)
        gradient_words.shift(LEFT)

        anti_arrow = new_arrow.copy()
        anti_arrow.rotate(np.pi, about_point = dot.get_center())
        anti_arrow.highlight(RED)

        self.play(
            Transform(arrow, new_arrow),
            Animation(dot),
            *[FadeOut(a) for a in arrows if a is not arrow]
        )
        self.play(FadeIn(gradient))
        self.play(Write(gradient_words, run_time = 2))
        self.dither(2)
        self.play(
            arrow.fade,
            ReplacementTransform(
                arrow.copy(),
                anti_arrow
            )
        )
        self.dither(2)

class CostSurface(ExternallyAnimatedScene):
    pass

class KhanAcademyMVCWrapper(PiCreatureScene):
    def construct(self):
        screen = ScreenRectangle(height = 5)
        screen.to_corner(UP+LEFT)
        morty = self.pi_creature

        self.play(
            ShowCreation(screen),
            morty.change, "raise_right_hand",
        )
        self.dither(3)
        self.play(morty.change, "happy", screen)
        self.dither(5)

class ShowFullCostFunctionGradient(PreviewLearning):
    def construct(self):
        self.organize_weights_as_column_vector()
        self.show_gradient()

    def organize_weights_as_column_vector(self):
        network_mob = self.network_mob
        edges = VGroup(*it.chain(*network_mob.edge_groups))
        layers = VGroup(*network_mob.layers)
        layers.add(network_mob.output_labels)
        self.color_network_edges()

        nums = [2.25, -1.57,  1.98, -1.16,  3.82, 1.21]
        decimals = VGroup(*[
            DecimalNumber(num).highlight(
                BLUE_D if num > 0 else RED
            )
            for num in nums
        ])
        dots = TexMobject("\\vdots")
        decimals.submobjects.insert(3, dots)
        decimals.arrange_submobjects(DOWN)
        decimals.shift(2*LEFT + 0.5*DOWN)
        lb, rb = brackets = TexMobject("\\big[", "\\big]")
        brackets.scale(2)
        brackets.stretch_to_fit_height(1.2*decimals.get_height())
        lb.next_to(decimals, LEFT, SMALL_BUFF)
        rb.next_to(decimals, RIGHT, SMALL_BUFF)
        column_vect = VGroup(lb, decimals, rb)

        edges_target = VGroup(*it.chain(
            decimals[:3],
            [dots]*(len(edges) - 6),
            decimals[-3:]
        ))

        words = TextMobject("$13{,}002$ weights and biases")
        words.next_to(column_vect, UP)

        lhs = TexMobject("\\vec{\\textbf{W}}", "=")
        lhs[0].highlight(YELLOW)
        lhs.next_to(column_vect, LEFT)

        self.play(
            FadeOut(layers),
            edges.space_out_submobjects, 1.2,
        )
        self.play(
            ReplacementTransform(
                edges, edges_target,
                run_time = 2,
                submobject_mode = "lagged_start"
            ),
            LaggedStart(FadeIn, words),
        )
        self.play(*map(Write, [lb, rb, lhs]), run_time = 1)
        self.dither()

        self.column_vect = column_vect

    def show_gradient(self):
        column_vect = self.column_vect

        lhs = TexMobject(
            "-", "\\nabla", "C(", "\\vec{\\textbf{W}}", ")", "="
        )
        lhs.shift(2*RIGHT)
        lhs.highlight_by_tex("W", YELLOW)
        old_decimals = VGroup(*filter(
            lambda m : isinstance(m, DecimalNumber),
            column_vect[1]
        ))
        new_decimals = VGroup()
        new_nums = [0.18, 0.45, -0.51, 0.4, -0.32, 0.82]
        for decimal, new_num in zip(old_decimals, new_nums):
            new_decimal = DecimalNumber(new_num)
            new_decimal.highlight(BLUE if new_num > 0 else RED_B)
            new_decimal.move_to(decimal)
            new_decimals.add(new_decimal)
        rhs = VGroup(
            column_vect[0].copy(),
            new_decimals, 
            column_vect[2].copy(),
        )
        rhs.to_edge(RIGHT, buff = 1.75)
        lhs.next_to(rhs, LEFT)

        words = TextMobject("How to nudge all \\\\ weights and biases")
        words.next_to(rhs, UP)

        self.play(Write(VGroup(lhs, rhs)))
        self.play(FadeIn(words))
        for od, nd in zip(old_decimals, new_decimals):
            nd = nd.deepcopy()
            od_num = od.number
            nd_num = nd.number
            self.play(
                nd.move_to, od, 
                nd.shift, 1.5*RIGHT
            )
            self.play(
                Transform(
                    nd, VectorizedPoint(od.get_center()),
                    submobject_mode = "lagged_start",
                    remover = True
                ),
                ChangingDecimal(
                    od,
                    lambda a : interpolate(od_num, od_num+nd_num, a)
                )
            )
        self.dither()

class HowMinimizingCostMeansBetterTrainingPerformance(IntroduceCostFunction):
    def construct(self):
        IntroduceCostFunction.construct(self)
        self.improve_last_layer()

    def improve_last_layer(self):
        decimals = self.decimal_groups[0]
        neurons = self.network_mob.layers[-1].neurons

        values = [d.number for d in decimals]
        target_values = 0.1*np.random.random(10)
        target_values[3] = 0.98

        words = TextMobject("Minimize cost $\\dots$")
        words.next_to(decimals, UP, MED_LARGE_BUFF)
        words.highlight(YELLOW)
        # words.shift(LEFT)

        def generate_update(n1, n2):
            return lambda a : interpolate(n1, n2, a)
        updates = [
            generate_update(n1, n2)
            for n1, n2 in zip(values, target_values)
        ]

        self.play(LaggedStart(FadeIn, words, run_time = 1))
        self.play(*[
            ChangingDecimal(d, update)
            for d, update in zip(decimals, updates)
        ] + [
            UpdateFromFunc(
                d,
                lambda mob: mob.set_fill(
                    interpolate_color(BLACK, WHITE, 0.5+0.5*mob.number),
                    opacity = 1
                )
            )
            for d in decimals
        ] + [
            ApplyMethod(neuron.set_fill, WHITE, target_value)
            for neuron, target_value in zip(neurons, target_values)
        ], run_time = 3)
        self.dither()

    ###

    def average_over_all_training_data(self):
        pass #So that IntroduceCostFunction.construct doesn't do this

class CostSurfaceSteps(ExternallyAnimatedScene):
    pass

class ConfusedAboutHighDimension(TeacherStudentsScene):
    def construct(self):
        self.student_says(
            "13{,}002-dimensional \\\\ nudge?",
            target_mode = "confused"
        )
        self.change_student_modes(*["confused"]*3)
        self.dither(2)
        self.teacher_thinks(
            "",
            bubble_kwargs = {"width" : 6, "height" : 4},
            added_anims = [self.get_student_changes(*["plain"]*3)]
        )
        self.zoom_in_on_thought_bubble()

class NonSpatialGradientIntuition(Scene):
    CONFIG = {
        "w_color" : YELLOW,
        "positive_color" : BLUE,
        "negative_color" : RED,
        "vect_height" : SPACE_HEIGHT - MED_LARGE_BUFF,
        "text_scale_value" : 0.7,
    }
    def construct(self):
        self.add_vector()
        self.add_gradient()
        self.show_sign_interpretation()
        self.show_magnitude_interpretation()

    def add_vector(self):
        lhs = TexMobject("\\vec{\\textbf{W}}", "=")
        lhs[0].highlight(self.w_color)
        lhs.to_edge(LEFT)

        ws = VGroup(*[
            VGroup(TexMobject(tex))
            for tex in it.chain(
                ["w_%d"%d for d in range(3)],
                ["\\vdots"],
                ["w_{13{,}00%d}"%d for d in range(3)]
            )
        ])
        ws.highlight(self.w_color)
        ws.arrange_submobjects(DOWN)
        lb, rb = brackets = TexMobject("\\big[", "\\big]").scale(2)
        brackets.stretch_to_fit_height(1.2*ws.get_height())
        lb.next_to(ws, LEFT)
        rb.next_to(ws, RIGHT)
        vect = VGroup(lb, ws, rb)

        vect.scale_to_fit_height(self.vect_height)
        vect.to_edge(UP).shift(2*LEFT)
        lhs.next_to(vect, LEFT)

        self.add(lhs, vect)
        self.vect = vect
        self.top_lhs = lhs

    def add_gradient(self):
        lb, ws, rb = vect = self.vect
        ws = VGroup(*ws)
        dots = ws[len(ws)/2]
        ws.remove(dots)

        lhs = TexMobject(
            "-\\nabla", "C(", "\\vec{\\textbf{W}}", ")", "="
        )
        lhs.next_to(vect, RIGHT, LARGE_BUFF)
        lhs.highlight_by_tex("W", self.w_color)

        decimals = VGroup()
        nums = [0.31, 0.03, -1.25, 0.78, -0.37, 0.16]
        for num, w in zip(nums, ws):
            decimal = DecimalNumber(num)
            decimal.scale(self.text_scale_value)
            if num > 0:
                decimal.highlight(self.positive_color)
            else:
                decimal.highlight(self.negative_color)
            decimal.move_to(w)
            decimals.add(decimal)
        new_dots = dots.copy()

        grad_content = VGroup(*it.chain(
            decimals[:3], new_dots, decimals[3:]
        ))
        grad_vect = VGroup(lb.copy(), grad_content, rb.copy())
        VGroup(grad_vect[0], grad_vect[-1]).space_out_submobjects(0.8)
        grad_vect.scale_to_fit_height(self.vect_height)
        grad_vect.next_to(self.vect, DOWN)
        lhs.next_to(grad_vect, LEFT)

        brace = Brace(grad_vect, RIGHT)
        words = brace.get_text("Example gradient")

        self.dither()
        self.play(
            ReplacementTransform(self.top_lhs.copy(), lhs),
            ReplacementTransform(self.vect.copy(), grad_vect),
            GrowFromCenter(brace),
            FadeIn(words)
        )
        self.dither()
        self.play(FadeOut(VGroup(brace, words)))

        self.ws = ws
        self.grad_lhs = lhs
        self.grad_vect = grad_vect
        self.decimals = decimals

    def show_sign_interpretation(self):
        ws = self.ws.copy()
        decimals = self.decimals

        direction_phrases = VGroup()
        for w, decimal in zip(ws, decimals):
            if decimal.number > 0:
                verb = "increase"
                color = self.positive_color
            else:
                verb = "decrease"
                color = self.negative_color
            phrase = TextMobject("should", verb)
            phrase.scale(self.text_scale_value)
            phrase.highlight_by_tex(verb, color)
            w.generate_target()
            group = VGroup(w.target, phrase)
            group.arrange_submobjects(RIGHT)
            w.target.shift(0.7*SMALL_BUFF*DOWN)
            group.move_to(decimal.get_center() + RIGHT, LEFT)
            direction_phrases.add(phrase)

        self.play(
            LaggedStart(MoveToTarget, ws),
            LaggedStart(FadeIn, direction_phrases)
        )
        self.dither(2)

        self.direction_phrases = direction_phrases
        self.ws = ws

    def show_magnitude_interpretation(self):
        direction_phrases = self.direction_phrases
        ws = self.ws
        decimals = self.decimals

        magnitude_words = VGroup()
        rects = VGroup()
        for phrase, decimal in zip(direction_phrases, decimals):
            if abs(decimal.number) < 0.2:
                adj = "a little"
                color = interpolate_color(BLACK, WHITE, 0.5)
            elif abs(decimal.number) < 0.5:
                adj = "somewhat"
                color = LIGHT_GREY
            else:
                adj = "a lot"
                color =  WHITE
            words = TextMobject(adj)
            words.scale(self.text_scale_value)
            words.highlight(color)
            words.next_to(phrase, RIGHT, SMALL_BUFF)
            magnitude_words.add(words)

            rect = SurroundingRectangle(
                VGroup(*decimal[-4:]), 
                buff = SMALL_BUFF,
                color = LIGHT_GREY
            )
            rect.target = words
            rects.add(rect)

        self.play(LaggedStart(ShowCreation, rects))
        self.play(LaggedStart(MoveToTarget, rects))
        self.dither(2)

class SomeConnectionsMatterMoreThanOthers(PreviewLearning):
    def setup(self):
        np.random.seed(1)
        PreviewLearning.setup(self)
        self.color_network_edges()

        ex_in = get_organized_images()[3][4]
        image = MNistMobject(ex_in)
        image.to_corner(UP+LEFT)
        self.add(image)
        self.ex_in = ex_in

    def construct(self):
        self.activate_network(self.ex_in)
        self.fade_edges()
        self.show_important_connection()
        self.show_unimportant_connection()

    def fade_edges(self):
        edges = VGroup(*it.chain(*self.network_mob.edge_groups))
        self.play(*[
            ApplyMethod(
                edge.set_stroke, BLACK, 0,
                rate_func = lambda a : 0.5*smooth(a)
            )
            for edge in edges
        ])

    def show_important_connection(self):
        layers = self.network_mob.layers
        edge = self.get_edge(2, 3)
        edge.set_stroke(YELLOW, 4)
        words = TextMobject("This weight \\\\ matters a lot")
        words.next_to(layers[-1], UP).to_edge(UP)
        words.highlight(YELLOW)
        arrow = Arrow(words.get_bottom(), edge.get_center())

        self.play(
            ShowCreation(edge),
            GrowArrow(arrow),
            FadeIn(words)
        )
        self.dither()

    def show_unimportant_connection(self):
        color = TEAL
        edge = self.get_edge(11, 6)
        edge.set_stroke(color, 5)
        words = TextMobject("Who even cares \\\\ about this weight?")
        words.next_to(self.network_mob.layers[-1], DOWN)
        words.to_edge(DOWN)
        words.highlight(color)
        arrow = Arrow(words.get_top(), edge.get_center(), buff = SMALL_BUFF)
        arrow.highlight(color)

        self.play(
            ShowCreation(edge),
            GrowArrow(arrow),
            FadeIn(words)
        )
        self.dither()
    ###

    def get_edge(self, i1, i2):
        layers = self.network_mob.layers
        n1 = layers[-2].neurons[i1]
        n2 = layers[-1].neurons[i2]
        return self.network_mob.get_edge(n1, n2)

class TwoGradientInterpretationsIn2D(Scene):
    def construct(self):
        self.setup_plane()
        self.add_function_definitions()
        self.point_out_direction()
        self.point_out_relative_importance()

    def setup_plane(self):
        plane = NumberPlane()
        plane.add_coordinates()
        self.add(plane)
        self.plane = plane

    def add_function_definitions(self):
        func = TexMobject(
            "C(", "x, y", ")", "=", 
            "\\frac{3}{2}x^2", "+", "\\frac{1}{2}y^2",
        )
        func.shift(SPACE_WIDTH*LEFT/2).to_edge(UP)

        grad = TexMobject("\\nabla", "C(", "1, 1", ")", "=")
        vect = TexMobject(
            "\\left[\\begin{array}{c} 3 \\\\ 1 \\end{array}\\right]"
        )
        vect.next_to(grad, RIGHT, SMALL_BUFF)
        grad_group = VGroup(grad, vect)
        grad_group.next_to(ORIGIN, RIGHT).to_edge(UP, buff = MED_SMALL_BUFF)
        # grad_group.next_to(func, DOWN)
        # for mob in grad, func:
        #     mob.highlight_by_tex("C(", RED)
        #     mob.highlight_by_tex(")", RED)
        for mob in grad, vect, func:
            mob.add_background_rectangle()
            mob.background_rectangle.scale_in_place(1.1)

        self.play(Write(func, run_time = 1))
        self.play(Write(grad_group, run_time = 2))
        self.dither()

        self.func = func
        self.grad = grad
        self.vect = vect

    def point_out_direction(self):
        coords = self.grad.get_part_by_tex("1, 1").copy()
        vect = self.vect[1].copy()
        coords.highlight(YELLOW)
        vect.highlight(GREEN)

        dot = Dot(self.plane.coords_to_point(1, 1))
        dot.highlight(coords.get_color())
        arrow = Arrow(
            self.plane.coords_to_point(1, 1),
            self.plane.coords_to_point(4, 2),
            buff = 0,
            color = vect.get_color()
        )
        words = TextMobject("Direction of \\\\ steepest ascent")
        words.add_background_rectangle()
        words.next_to(ORIGIN, DOWN)
        words.rotate(arrow.get_angle())
        words.shift(arrow.get_center())

        self.play(DrawBorderThenFill(coords, run_time = 1))
        self.play(ReplacementTransform(coords.copy(), dot))
        self.play(DrawBorderThenFill(vect, run_time = 1))
        self.play(
            ReplacementTransform(vect.copy(), arrow),
            Animation(dot)
        )
        self.play(Write(words))
        self.dither()

        self.remove(vect)
        self.vect[1].highlight(vect.get_color())
        self.remove(coords)
        self.grad.get_part_by_tex("1, 1").highlight(coords.get_color())

    def point_out_relative_importance(self):
        func = self.func
        grad_group = VGroup(self.grad, self.vect)
        x_part = func.get_part_by_tex("x^2")
        y_part = func.get_part_by_tex("y^2")

        self.play(func.shift, 1.5*DOWN)

        x_rect = SurroundingRectangle(x_part, color = YELLOW)
        y_rect = SurroundingRectangle(y_part, color = TEAL)
        x_words = TextMobject("$x$ has 3 times \\\\ the impact...")
        x_words.highlight(x_rect.get_color())
        x_words.add_background_rectangle()
        x_words.next_to(x_rect, UP)
        # x_words.to_edge(LEFT)
        y_words = TextMobject("...as $y$")
        y_words.highlight(y_rect.get_color())
        y_words.add_background_rectangle()
        y_words.next_to(y_rect, DOWN)

        self.play(
            Write(x_words, run_time = 2),
            ShowCreation(x_rect)
        )
        self.dither()
        self.play(
            Write(y_words, run_time = 1),
            ShowCreation(y_rect)
        )
        self.dither(2)

class ParaboloidGraph(ExternallyAnimatedScene):
    pass

class TODOInsertEmphasizeComplexityOfCostFunctionCopy(TODOStub):
    CONFIG = {
        "message" : "Insert EmphasizeComplexityOfCostFunction copy"
    }

class GradientNudging(PreviewLearning):
    CONFIG = {
        "n_steps" : 10
    }
    def construct(self):
        self.setup_network_mob()
        self.add_gradient()
        self.change_weights_repeatedly()

    def setup_network_mob(self):
        network_mob = self.network_mob
        self.color_network_edges()
        network_mob.scale(0.7)
        network_mob.to_corner(DOWN+RIGHT)

    def add_gradient(self):
        lhs = TexMobject(
            "-", "\\nabla", "C(", "\\dots", ")", "="
        )
        lhs.to_edge(LEFT)
        brace = Brace(lhs.get_part_by_tex("dots"), DOWN)
        words = brace.get_text("All weights \\\\ and biases")
        words.scale(0.8, about_point = words.get_top())
        np.random.seed(3)
        nums = 4*(np.random.random(8)-0.5)
        vect = get_decimal_vector(nums)
        vect.next_to(lhs, RIGHT)

        self.add(lhs, brace, words, vect)

        self.grad_vect = vect

    def change_weights_repeatedly(self):
        network_mob = self.network_mob
        edges = VGroup(*reversed(list(
            it.chain(*network_mob.edge_groups)
        )))

        decimals = self.grad_vect.decimals

        words = TextMobject(
            "Change by some small\\\\",
            "multiple of $-\\nabla C(\\dots)$"
        )
        words.next_to(network_mob, UP).to_edge(UP)
        arrows = VGroup(*[
            Arrow(
                words.get_bottom(),
                edge_group.get_top(),
                color = WHITE
            )
            for edge_group in network_mob.edge_groups
        ])

        self.play(
            ReplacementTransform(
                decimals.copy().set_fill(opacity = 0).set_stroke(width = 1), 
                self.network_mob.edge_groups
            ),
            FadeIn(words),
            LaggedStart(GrowArrow, arrows, run_time = 1)
        )
        self.play(self.get_edge_change_anim(edges))
        self.play(*self.get_decimal_change_anims(decimals))
        for x in range(self.n_steps):
            self.play(self.get_edge_change_anim(edges))
            self.play(*self.get_decimal_change_anims(decimals))
        self.dither()

    ###

    def get_edge_change_anim(self, edges):
        target_nums = 6*(np.random.random(len(edges))-0.5)
        edges.generate_target()
        for edge, target_num in zip(edges.target, target_nums):
            curr_num = edge.get_stroke_width()
            if Color(edge.get_stroke_color()) == Color(self.negative_edge_color):
                curr_num *= -1
            new_num = interpolate(curr_num, target_num, 0.2)
            if new_num > 0:
                new_color = self.positive_edge_color
            else:
                new_color = self.negative_edge_color
            edge.set_stroke(new_color, abs(new_num))
            edge.rotate_in_place(np.pi)
        return MoveToTarget(
            edges,
            submobject_mode = "lagged_start",
            lag_factor = 8,
            run_time = 1.5
        )

    def get_decimal_change_anims(self, decimals):
        changes = 0.2*(np.random.random(len(decimals))-0.5)
        def generate_change_func(x, dx):
            return lambda a : interpolate(x, x+dx, a)
        return [
            ChangingDecimal(
                decimal, 
                generate_change_func(decimal.number, change)
            )
            for decimal, change in zip(decimals, changes)
        ]

class BackPropWrapper(PiCreatureScene):
    def construct(self):
        morty = self.pi_creature
        screen = ScreenRectangle(height = 5)
        screen.to_corner(UP+LEFT)
        screen.shift(MED_LARGE_BUFF*DOWN)

        title = TextMobject("Backpropagation", "(next video)")
        title.next_to(screen, UP)

        self.play(
            morty.change, "raise_right_hand", screen,
            ShowCreation(screen)
        )
        self.play(Write(title[0], run_time = 1))
        self.dither()
        self.play(Write(title[1], run_time = 1))
        self.play(morty.change, "happy", screen)
        self.dither(5)

class TODOInsertCostSurfaceSteps(TODOStub):
    CONFIG = {
        "message" : "Insert CostSurfaceSteps"
    }

class ContinuouslyRangingNeuron(PreviewLearning):
    def construct(self):
        self.color_network_edges()
        network_mob = self.network_mob
        network_mob.scale(0.8)
        network_mob.to_edge(DOWN)
        neuron = self.network_mob.layers[2].neurons[6]
        decimal = DecimalNumber(0)
        decimal.scale_to_fit_width(0.8*neuron.get_width())
        decimal.move_to(neuron)

        decimal.generate_target()
        neuron.generate_target()
        group = VGroup(neuron.target, decimal.target)
        group.scale_to_fit_height(1)
        group.next_to(network_mob, UP)
        decimal.set_fill(opacity = 0)

        def update_decimal_color(decimal):
            if neuron.get_fill_opacity() > 0.8:
                decimal.highlight(BLACK)
            else:
                decimal.highlight(WHITE)
        decimal_color_anim = UpdateFromFunc(decimal, update_decimal_color)

        self.play(*map(MoveToTarget, [neuron, decimal]))
        for x in 0.7, 0.35, 0.97, 0.23, 0.54:
            curr_num = neuron.get_fill_opacity()
            self.play(
                neuron.set_fill, None, x,
                ChangingDecimal(
                    decimal, lambda a : interpolate(curr_num, x, a)
                ),
                decimal_color_anim
            )
            self.dither()

class AskHowItDoes(TeacherStudentsScene):
    def construct(self):
        self.student_says(
            "How well \\\\ does it do?",
            student_index = 0
        )
        self.dither(5)

class TestPerformance(PreviewLearning):
    CONFIG = {
        "n_examples" : 200,
        "time_per_example" : 0.1,
        "wrong_dither_time" : 0.5
    }
    def construct(self):
        self.init_testing_data()
        self.add_title()
        self.add_fraction()
        self.run_through_examples()

    def init_testing_data(self):
        training_data, validation_data, test_data = load_data_wrapper()
        self.test_data = iter(test_data[:self.n_examples])

    def add_title(self):
        title = TextMobject("Testing data")
        title.to_corner(UP+LEFT)
        self.add(title)

    def add_fraction(self):
        self.n_correct = 0
        self.total = 0
        self.decimal = DecimalNumber(0)
        word_frac = TexMobject(
            "{\\text{Number correct}", "\\over", 
            "\\text{total}}", "=",
        )
        word_frac[0].highlight(GREEN)
        self.frac = self.get_frac()
        self.equals = TexMobject("=")
        fracs = VGroup(
            word_frac, self.frac, 
            self.equals, self.decimal
        )
        fracs.arrange_submobjects(RIGHT)
        fracs.to_edge(UP)
        self.add(fracs)

    def run_through_examples(self):
        rects = [
            SurroundingRectangle(VGroup(neuron, label))
            for neuron, label in zip(
                self.network_mob.layers[-1].neurons,
                self.network_mob.output_labels
            )
        ]
        wrong = TextMobject("Wrong!")
        wrong.highlight(RED)


        for test_in, test_out in self.test_data:
            self.total += 1
            image = MNistMobject(test_in)
            image.to_edge(LEFT)
            image.shift(UP)
            self.add(image)

            activations = self.activate_layers(test_in)
            choice = np.argmax(activations[-1])
            rect = rects[choice]
            self.add(rect)

            correct = (choice == test_out)
            if correct:
                self.n_correct += 1
            else:
                wrong.next_to(rect, RIGHT)
                self.add(wrong)
            new_frac = self.get_frac()
            new_frac.shift(
                self.frac[1].get_left() - \
                new_frac[1].get_left()
            )
            self.remove(self.frac)
            self.add(new_frac)
            self.frac = new_frac
            self.equals.next_to(new_frac, RIGHT)

            new_decimal = DecimalNumber(float(self.n_correct)/self.total)
            new_decimal.next_to(self.equals, RIGHT)
            self.remove(self.decimal)
            self.add(new_decimal)
            self.decimal = new_decimal

            self.dither(self.time_per_example)
            if not correct:
                self.dither(self.wrong_dither_time)

            self.remove(rect, wrong, image)

        self.add(rect, image)

    ###
    def add_network(self):
        self.network_mob = MNistNetworkMobject(**self.network_mob_config)
        self.network_mob.scale(0.8)
        self.network_mob.to_edge(DOWN)
        self.network = self.network_mob.neural_network
        self.add(self.network_mob)
        self.color_network_edges()

    def get_frac(self):
        frac = TexMobject("{%d"%self.n_correct, "\\over", "%d}"%self.total)
        frac[0].highlight(GREEN)
        return frac

    def activate_layers(self, test_in):
        activations = self.network.get_activation_of_all_layers(test_in)
        layers = self.network_mob.layers
        for layer, activation in zip(layers, activations)[1:]:
            for neuron, a in zip(layer.neurons, activation):
                neuron.set_fill(opacity = a)
        return activations

class ReactToPerformance(TeacherStudentsScene):
    def construct(self):
        title = VGroup(
            TextMobject("Play with network structure"),
            Arrow(LEFT, RIGHT, color = WHITE),
            TextMobject("98\\%", "testing accuracy")
        )
        title.arrange_submobjects(RIGHT)
        title.to_edge(UP)
        title[-1][0].highlight(GREEN)
        self.play(Write(title, run_time = 2))

        last_words = TextMobject(
            "State of the art \\\\ is", 
            "99.79\\%"
        )
        last_words[-1].highlight(GREEN)

        self.teacher_says(
            "That's pretty", "good!",
            target_mode = "surprised",
            run_time = 1
        )
        self.change_student_modes(*["hooray"]*3)
        self.dither()
        self.teacher_says(last_words, target_mode = "hesitant")
        self.change_student_modes(
            *["pondering"]*3,
            look_at_arg = self.teacher.bubble
        )
        self.dither()

class WrongExamples(TestPerformance):
    CONFIG = {
        "time_per_example" : 0
    }

class TODOBreakUpNineByPatterns(TODOStub):
    CONFIG = {
        "message" : "Insert the scene with 9 \\\\ broken up by patterns"
    }

class NotAtAll(TeacherStudentsScene, PreviewLearning):
    def setup(self):
        TeacherStudentsScene.setup(self)
        PreviewLearning.setup(self)

    def construct(self):
        words = TextMobject("Well...\\\\", "not at all!")
        words[1].highlight(BLACK)
        network_mob = self.network_mob
        network_mob.scale_to_fit_height(4)
        network_mob.to_corner(UP+LEFT)
        self.add(network_mob)
        self.color_network_edges()

        self.teacher_says(
            words, target_mode = "guilty",
            run_time = 1
        )
        self.change_student_modes(*["sassy"]*3)
        self.play(
            self.teacher.change, "concerned_musician",
            words[1].highlight, WHITE
        )
        self.dither(2)

class InterpretFirstWeightMatrixRows(TestPerformance):
    CONFIG = {
        "stroke_width_exp" : 1,
    }
    def construct(self):
        self.slide_network_to_side()
        self.prepare_pixel_arrays()
        self.show_all_pixel_array()

    def slide_network_to_side(self):
        network_mob = self.network_mob
        network_mob.generate_target()
        to_fade = VGroup(*it.chain(
            network_mob.edge_groups[1:],
            network_mob.layers[2:],
            network_mob.output_labels
        ))
        to_keep = VGroup(*it.chain(
            network_mob.edge_groups[0],
            network_mob.layers[:2]
        ))
        shift_val = SPACE_WIDTH*LEFT + MED_LARGE_BUFF*RIGHT - \
                    to_keep.get_left()
        self.play(
            to_fade.shift, shift_val,
            to_fade.fade, 1,
            to_keep.shift, shift_val
        )
        self.remove(to_fade)

    def prepare_pixel_arrays(self):
        pixel_arrays = VGroup()
        w_matrix = self.network.weights[0]
        for row in w_matrix:
            max_val = np.max(np.abs(row))
            shades = np.array(row)/max_val
            pixel_array = PixelsFromVect(np.zeros(row.size))
            for pixel, shade in zip(pixel_array, shades):
                if shade > 0:
                    color = self.positive_edge_color
                else:
                    color = self.negative_edge_color
                pixel.set_fill(color, opacity = abs(shade)**(0.3))
            pixel_arrays.add(pixel_array)
        pixel_arrays.arrange_submobjects_in_grid(buff = MED_LARGE_BUFF)
        pixel_arrays.scale_to_fit_height(2*SPACE_HEIGHT - 2.5)
        pixel_arrays.to_corner(DOWN+RIGHT)

        for pixel_array in pixel_arrays:
            rect = SurroundingRectangle(pixel_array)
            rect.highlight(WHITE)
            pixel_array.rect = rect

        words = TextMobject("What second layer \\\\ neurons look for")
        words.next_to(pixel_arrays, UP).to_edge(UP)

        self.pixel_arrays = pixel_arrays
        self.words = words

    def show_all_pixel_array(self):
        edges = self.network_mob.edge_groups[0]
        neurons = self.network_mob.layers[1].neurons
        edges.remove(neurons[0].edges_in)

        self.play(
            VGroup(*neurons[1:]).set_stroke, None, 0.5,
            FadeIn(self.words),
            neurons[0].edges_in.set_stroke, None, 2,
            *[
                ApplyMethod(edge.set_stroke, None, 0.25)
                for edge in edges
                if edge not in neurons[0].edges_in
            ]
        )
        self.dither()
        last_neuron = None

        for neuron, pixel_array in zip(neurons, self.pixel_arrays):
            if last_neuron:
                self.play(
                    last_neuron.edges_in.set_stroke, None, 0.25,
                    last_neuron.set_stroke, None, 0.5,
                    neuron.set_stroke, None, 3,
                    neuron.edges_in.set_stroke, None, 2,
                )
            self.play(ReplacementTransform(
                neuron.edges_in.copy().set_fill(opacity = 0),
                pixel_array,
            ))
            self.play(ShowCreation(pixel_array.rect))
            last_neuron = neuron

class InputRandomData(TestPerformance):
    def construct(self):
        self.color_network_edges()
        self.show_random_image()
        self.show_expected_outcomes()
        self.feed_in_random_data()
        self.network_speaks()

    def show_random_image(self):
        np.random.seed(4)
        rand_vect = np.random.random(28*28)
        image = PixelsFromVect(rand_vect)
        image.to_edge(LEFT)
        image.shift(UP)
        rect = SurroundingRectangle(image)

        arrow = Arrow(
            rect.get_top(),
            self.network_mob.layers[0].neurons.get_top(),
            path_arc = -2*np.pi/3,
            use_rectangular_stem = False,
        )
        arrow.tip.set_stroke(width = 3)

        self.play(
            ShowCreation(rect),
            LaggedStart(
                DrawBorderThenFill, image, 
                stroke_width = 0.5
            )
        )
        self.play(ShowCreation(arrow))
        self.dither()

        self.image = image
        self.rand_vect = rand_vect
        self.image_rect = rect
        self.arrow = arrow

    def show_expected_outcomes(self):
        neurons = self.network_mob.layers[-1].neurons

        words = TextMobject("What might you expect?")
        words.to_corner(UP+RIGHT)
        arrow = Arrow(
            words.get_bottom(), neurons.get_top(),
            color = WHITE
        )

        self.play(
            Write(words, run_time = 1),
            GrowArrow(arrow)
        )
        vects = [np.random.random(10) for x in range(2)]
        vects += [np.zeros(10), 0.4*np.ones(10)]
        for vect in vects:
            neurons.generate_target()
            for neuron, o in zip(neurons, vect):
                neuron.generate_target()
                neuron.target.set_fill(WHITE, opacity = o)
            self.play(LaggedStart(
                MoveToTarget, neurons,
                run_time = 1
            ))
            self.dither()
        self.play(FadeOut(VGroup(words, arrow)))

    def feed_in_random_data(self):
        neurons = self.network_mob.layers[0].neurons
        rand_vect = self.rand_vect
        image = self.image.copy()
        output_labels = self.network_mob.output_labels

        opacities = it.chain(rand_vect[:8], rand_vect[-8:])
        target_neurons = neurons.copy()
        for n, o in zip(target_neurons, opacities):
            n.set_fill(WHITE, opacity = o)

        point = VectorizedPoint(neurons.get_center())
        image.target = VGroup(*it.chain(
            target_neurons[:len(neurons)/2],
            [point]*(len(image) - len(neurons)),
            target_neurons[-len(neurons)/2:]
        ))

        self.play(MoveToTarget(
            image, 
            run_time = 2,
            submobject_mode = "lagged_start"
        ))
        self.activate_network(rand_vect, FadeOut(image))

        ### React ###
        neurons = self.network_mob.layers[-1].neurons
        choice = np.argmax([n.get_fill_opacity() for n in neurons])
        rect = SurroundingRectangle(VGroup(
            neurons[choice], output_labels[choice]
        ))
        word = TextMobject("What?!?")
        word.highlight(YELLOW)
        word.next_to(rect, RIGHT)

        self.play(ShowCreation(rect))
        self.play(Write(word, run_time = 1))
        self.dither()

        self.network_mob.add(rect, word)
        self.choice = choice

    def network_speaks(self):
        network_mob = self.network_mob
        network_mob.generate_target(use_deepcopy = True)
        network_mob.target.scale(0.7)
        network_mob.target.to_edge(DOWN)
        eyes = Eyes(
            network_mob.target.edge_groups[1],
            height = 0.45,
        )
        eyes.shift(0.5*SMALL_BUFF*UP)

        bubble = SpeechBubble(
            height = 3, width = 5,
            direction = LEFT
        )
        bubble.pin_to(network_mob.target.edge_groups[-1])
        bubble.write("Looks like a \\\\ %d to me!"%self.choice)

        self.play(
            MoveToTarget(network_mob),
            FadeIn(eyes)
        )
        self.play(eyes.look_at_anim(self.image))
        self.play(
            ShowCreation(bubble),
            Write(bubble.content, run_time = 1)
        )
        self.play(eyes.blink_anim())
        self.dither()

class TODOShowCostFunctionDef(TODOStub):
    CONFIG = {
        "message" : "Insert cost function averaging portion"
    }





































