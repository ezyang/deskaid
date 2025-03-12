#!/usr/bin/env python3

import os
import re
import tempfile
import unittest
from unittest.mock import patch

from expecttest import TestCase

from codemcp.common import MAX_LINE_LENGTH, MAX_LINES_TO_READ
from codemcp.tools.read_file import read_file_content


class TestReadFile(TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Create a test file with known content
        self.test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        with open(self.test_file_path, "w") as f:
            for i in range(1, 101):
                f.write(f"This is line {i}\n")

        # Create a file with long lines
        self.long_line_file_path = os.path.join(
            self.temp_dir.name,
            "long_line_file.txt",
        )
        with open(self.long_line_file_path, "w") as f:
            f.write("Short line\n")
            f.write("A" * (MAX_LINE_LENGTH + 100) + "\n")
            f.write("Another short line\n")

        # Create a large file that exceeds the line limit
        self.large_file_path = os.path.join(self.temp_dir.name, "large_file.txt")
        with open(self.large_file_path, "w") as f:
            for i in range(1, MAX_LINES_TO_READ + 100):
                f.write(f"Line {i}\n")

        # Setup mock patches
        self.setup_mocks()

    def setup_mocks(self):
        """Setup mocks for git functions to bypass repository checks"""
        # Create patch for git repository check
        self.is_git_repo_patch = patch("codemcp.git.is_git_repository")
        self.mock_is_git_repo = self.is_git_repo_patch.start()
        self.mock_is_git_repo.return_value = True
        self.addCleanup(self.is_git_repo_patch.stop)

        # Create patch for git base directory
        self.git_base_dir_patch = patch("codemcp.access.get_git_base_dir")
        self.mock_git_base_dir = self.git_base_dir_patch.start()
        self.mock_git_base_dir.return_value = self.temp_dir.name
        self.addCleanup(self.git_base_dir_patch.stop)

        # Create a mock codemcp.toml file to satisfy permission check
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("[codemcp]\nenabled = true\n")

    def normalize_result(self, result):
        """Normalize temporary directory paths in the result.

        This replaces the actual temporary directory path with a fixed placeholder
        to make tests more stable across different runs.
        """
        if self.temp_dir and self.temp_dir.name:
            # Replace the actual temp dir path with a fixed placeholder
            return re.sub(re.escape(self.temp_dir.name), "/tmp/test_dir", result)
        return result

    def test_read_file_basic(self):
        """Test basic file reading functionality"""
        result = read_file_content(self.test_file_path)
        self.assertExpectedInline(
            self.normalize_result(result),
            """\
     1	This is line 1
     2	This is line 2
     3	This is line 3
     4	This is line 4
     5	This is line 5
     6	This is line 6
     7	This is line 7
     8	This is line 8
     9	This is line 9
    10	This is line 10
    11	This is line 11
    12	This is line 12
    13	This is line 13
    14	This is line 14
    15	This is line 15
    16	This is line 16
    17	This is line 17
    18	This is line 18
    19	This is line 19
    20	This is line 20
    21	This is line 21
    22	This is line 22
    23	This is line 23
    24	This is line 24
    25	This is line 25
    26	This is line 26
    27	This is line 27
    28	This is line 28
    29	This is line 29
    30	This is line 30
    31	This is line 31
    32	This is line 32
    33	This is line 33
    34	This is line 34
    35	This is line 35
    36	This is line 36
    37	This is line 37
    38	This is line 38
    39	This is line 39
    40	This is line 40
    41	This is line 41
    42	This is line 42
    43	This is line 43
    44	This is line 44
    45	This is line 45
    46	This is line 46
    47	This is line 47
    48	This is line 48
    49	This is line 49
    50	This is line 50
    51	This is line 51
    52	This is line 52
    53	This is line 53
    54	This is line 54
    55	This is line 55
    56	This is line 56
    57	This is line 57
    58	This is line 58
    59	This is line 59
    60	This is line 60
    61	This is line 61
    62	This is line 62
    63	This is line 63
    64	This is line 64
    65	This is line 65
    66	This is line 66
    67	This is line 67
    68	This is line 68
    69	This is line 69
    70	This is line 70
    71	This is line 71
    72	This is line 72
    73	This is line 73
    74	This is line 74
    75	This is line 75
    76	This is line 76
    77	This is line 77
    78	This is line 78
    79	This is line 79
    80	This is line 80
    81	This is line 81
    82	This is line 82
    83	This is line 83
    84	This is line 84
    85	This is line 85
    86	This is line 86
    87	This is line 87
    88	This is line 88
    89	This is line 89
    90	This is line 90
    91	This is line 91
    92	This is line 92
    93	This is line 93
    94	This is line 94
    95	This is line 95
    96	This is line 96
    97	This is line 97
    98	This is line 98
    99	This is line 99
   100	This is line 100""",
        )

    def test_read_file_with_offset(self):
        """Test reading a file with an offset"""
        result = read_file_content(self.test_file_path, offset=50)
        self.assertExpectedInline(
            self.normalize_result(result),
            """\
    50	This is line 50
    51	This is line 51
    52	This is line 52
    53	This is line 53
    54	This is line 54
    55	This is line 55
    56	This is line 56
    57	This is line 57
    58	This is line 58
    59	This is line 59
    60	This is line 60
    61	This is line 61
    62	This is line 62
    63	This is line 63
    64	This is line 64
    65	This is line 65
    66	This is line 66
    67	This is line 67
    68	This is line 68
    69	This is line 69
    70	This is line 70
    71	This is line 71
    72	This is line 72
    73	This is line 73
    74	This is line 74
    75	This is line 75
    76	This is line 76
    77	This is line 77
    78	This is line 78
    79	This is line 79
    80	This is line 80
    81	This is line 81
    82	This is line 82
    83	This is line 83
    84	This is line 84
    85	This is line 85
    86	This is line 86
    87	This is line 87
    88	This is line 88
    89	This is line 89
    90	This is line 90
    91	This is line 91
    92	This is line 92
    93	This is line 93
    94	This is line 94
    95	This is line 95
    96	This is line 96
    97	This is line 97
    98	This is line 98
    99	This is line 99
   100	This is line 100""",
        )

    def test_read_file_with_limit(self):
        """Test reading a file with a limit"""
        result = read_file_content(self.test_file_path, limit=10)
        self.assertExpectedInline(
            self.normalize_result(result),
            """\
     1	This is line 1
     2	This is line 2
     3	This is line 3
     4	This is line 4
     5	This is line 5
     6	This is line 6
     7	This is line 7
     8	This is line 8
     9	This is line 9
    10	This is line 10
... (file truncated, showing 10 of 100 lines)""",
        )

    def test_read_file_with_offset_and_limit(self):
        """Test reading a file with both offset and limit"""
        result = read_file_content(self.test_file_path, offset=50, limit=5)
        self.assertExpectedInline(
            self.normalize_result(result),
            """\
    50	This is line 50
    51	This is line 51
    52	This is line 52
    53	This is line 53
    54	This is line 54
... (file truncated, showing 5 of 100 lines)""",
        )

    def test_read_file_invalid_offset(self):
        """Test reading a file with an invalid offset"""
        result = read_file_content(self.test_file_path, offset=200)
        self.assertExpectedInline(
            self.normalize_result(result),
            """Error: Offset 200 is beyond the end of the file (total lines: 100)""",
        )

    def test_read_file_nonexistent(self):
        """Test reading a nonexistent file"""
        result = read_file_content(os.path.join(self.temp_dir.name, "nonexistent.txt"))
        normalized_result = self.normalize_result(result)
        self.assertExpectedInline(
            normalized_result,
            """Error: File does not exist: /tmp/test_dir/nonexistent.txt""",
        )

    def test_read_directory(self):
        """Test reading a directory instead of a file"""
        result = read_file_content(self.temp_dir.name)
        normalized_result = self.normalize_result(result)
        self.assertExpectedInline(
            normalized_result,
            """Error: Path is a directory, not a file: /tmp/test_dir""",
        )

    def test_read_file_long_lines(self):
        """Test reading a file with lines exceeding the maximum length"""
        result = read_file_content(self.long_line_file_path)
        self.assertExpectedInline(
            self.normalize_result(result),
            """\
     1	Short line
     2	AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA... (line truncated)
     3	Another short line""",
        )

    def test_read_large_file(self):
        """Test reading a large file that exceeds the line limit"""
        result = read_file_content(self.large_file_path)
        self.assertExpectedInline(
            self.normalize_result(result),
            """\
     1	Line 1
     2	Line 2
     3	Line 3
     4	Line 4
     5	Line 5
     6	Line 6
     7	Line 7
     8	Line 8
     9	Line 9
    10	Line 10
    11	Line 11
    12	Line 12
    13	Line 13
    14	Line 14
    15	Line 15
    16	Line 16
    17	Line 17
    18	Line 18
    19	Line 19
    20	Line 20
    21	Line 21
    22	Line 22
    23	Line 23
    24	Line 24
    25	Line 25
    26	Line 26
    27	Line 27
    28	Line 28
    29	Line 29
    30	Line 30
    31	Line 31
    32	Line 32
    33	Line 33
    34	Line 34
    35	Line 35
    36	Line 36
    37	Line 37
    38	Line 38
    39	Line 39
    40	Line 40
    41	Line 41
    42	Line 42
    43	Line 43
    44	Line 44
    45	Line 45
    46	Line 46
    47	Line 47
    48	Line 48
    49	Line 49
    50	Line 50
    51	Line 51
    52	Line 52
    53	Line 53
    54	Line 54
    55	Line 55
    56	Line 56
    57	Line 57
    58	Line 58
    59	Line 59
    60	Line 60
    61	Line 61
    62	Line 62
    63	Line 63
    64	Line 64
    65	Line 65
    66	Line 66
    67	Line 67
    68	Line 68
    69	Line 69
    70	Line 70
    71	Line 71
    72	Line 72
    73	Line 73
    74	Line 74
    75	Line 75
    76	Line 76
    77	Line 77
    78	Line 78
    79	Line 79
    80	Line 80
    81	Line 81
    82	Line 82
    83	Line 83
    84	Line 84
    85	Line 85
    86	Line 86
    87	Line 87
    88	Line 88
    89	Line 89
    90	Line 90
    91	Line 91
    92	Line 92
    93	Line 93
    94	Line 94
    95	Line 95
    96	Line 96
    97	Line 97
    98	Line 98
    99	Line 99
   100	Line 100
   101	Line 101
   102	Line 102
   103	Line 103
   104	Line 104
   105	Line 105
   106	Line 106
   107	Line 107
   108	Line 108
   109	Line 109
   110	Line 110
   111	Line 111
   112	Line 112
   113	Line 113
   114	Line 114
   115	Line 115
   116	Line 116
   117	Line 117
   118	Line 118
   119	Line 119
   120	Line 120
   121	Line 121
   122	Line 122
   123	Line 123
   124	Line 124
   125	Line 125
   126	Line 126
   127	Line 127
   128	Line 128
   129	Line 129
   130	Line 130
   131	Line 131
   132	Line 132
   133	Line 133
   134	Line 134
   135	Line 135
   136	Line 136
   137	Line 137
   138	Line 138
   139	Line 139
   140	Line 140
   141	Line 141
   142	Line 142
   143	Line 143
   144	Line 144
   145	Line 145
   146	Line 146
   147	Line 147
   148	Line 148
   149	Line 149
   150	Line 150
   151	Line 151
   152	Line 152
   153	Line 153
   154	Line 154
   155	Line 155
   156	Line 156
   157	Line 157
   158	Line 158
   159	Line 159
   160	Line 160
   161	Line 161
   162	Line 162
   163	Line 163
   164	Line 164
   165	Line 165
   166	Line 166
   167	Line 167
   168	Line 168
   169	Line 169
   170	Line 170
   171	Line 171
   172	Line 172
   173	Line 173
   174	Line 174
   175	Line 175
   176	Line 176
   177	Line 177
   178	Line 178
   179	Line 179
   180	Line 180
   181	Line 181
   182	Line 182
   183	Line 183
   184	Line 184
   185	Line 185
   186	Line 186
   187	Line 187
   188	Line 188
   189	Line 189
   190	Line 190
   191	Line 191
   192	Line 192
   193	Line 193
   194	Line 194
   195	Line 195
   196	Line 196
   197	Line 197
   198	Line 198
   199	Line 199
   200	Line 200
   201	Line 201
   202	Line 202
   203	Line 203
   204	Line 204
   205	Line 205
   206	Line 206
   207	Line 207
   208	Line 208
   209	Line 209
   210	Line 210
   211	Line 211
   212	Line 212
   213	Line 213
   214	Line 214
   215	Line 215
   216	Line 216
   217	Line 217
   218	Line 218
   219	Line 219
   220	Line 220
   221	Line 221
   222	Line 222
   223	Line 223
   224	Line 224
   225	Line 225
   226	Line 226
   227	Line 227
   228	Line 228
   229	Line 229
   230	Line 230
   231	Line 231
   232	Line 232
   233	Line 233
   234	Line 234
   235	Line 235
   236	Line 236
   237	Line 237
   238	Line 238
   239	Line 239
   240	Line 240
   241	Line 241
   242	Line 242
   243	Line 243
   244	Line 244
   245	Line 245
   246	Line 246
   247	Line 247
   248	Line 248
   249	Line 249
   250	Line 250
   251	Line 251
   252	Line 252
   253	Line 253
   254	Line 254
   255	Line 255
   256	Line 256
   257	Line 257
   258	Line 258
   259	Line 259
   260	Line 260
   261	Line 261
   262	Line 262
   263	Line 263
   264	Line 264
   265	Line 265
   266	Line 266
   267	Line 267
   268	Line 268
   269	Line 269
   270	Line 270
   271	Line 271
   272	Line 272
   273	Line 273
   274	Line 274
   275	Line 275
   276	Line 276
   277	Line 277
   278	Line 278
   279	Line 279
   280	Line 280
   281	Line 281
   282	Line 282
   283	Line 283
   284	Line 284
   285	Line 285
   286	Line 286
   287	Line 287
   288	Line 288
   289	Line 289
   290	Line 290
   291	Line 291
   292	Line 292
   293	Line 293
   294	Line 294
   295	Line 295
   296	Line 296
   297	Line 297
   298	Line 298
   299	Line 299
   300	Line 300
   301	Line 301
   302	Line 302
   303	Line 303
   304	Line 304
   305	Line 305
   306	Line 306
   307	Line 307
   308	Line 308
   309	Line 309
   310	Line 310
   311	Line 311
   312	Line 312
   313	Line 313
   314	Line 314
   315	Line 315
   316	Line 316
   317	Line 317
   318	Line 318
   319	Line 319
   320	Line 320
   321	Line 321
   322	Line 322
   323	Line 323
   324	Line 324
   325	Line 325
   326	Line 326
   327	Line 327
   328	Line 328
   329	Line 329
   330	Line 330
   331	Line 331
   332	Line 332
   333	Line 333
   334	Line 334
   335	Line 335
   336	Line 336
   337	Line 337
   338	Line 338
   339	Line 339
   340	Line 340
   341	Line 341
   342	Line 342
   343	Line 343
   344	Line 344
   345	Line 345
   346	Line 346
   347	Line 347
   348	Line 348
   349	Line 349
   350	Line 350
   351	Line 351
   352	Line 352
   353	Line 353
   354	Line 354
   355	Line 355
   356	Line 356
   357	Line 357
   358	Line 358
   359	Line 359
   360	Line 360
   361	Line 361
   362	Line 362
   363	Line 363
   364	Line 364
   365	Line 365
   366	Line 366
   367	Line 367
   368	Line 368
   369	Line 369
   370	Line 370
   371	Line 371
   372	Line 372
   373	Line 373
   374	Line 374
   375	Line 375
   376	Line 376
   377	Line 377
   378	Line 378
   379	Line 379
   380	Line 380
   381	Line 381
   382	Line 382
   383	Line 383
   384	Line 384
   385	Line 385
   386	Line 386
   387	Line 387
   388	Line 388
   389	Line 389
   390	Line 390
   391	Line 391
   392	Line 392
   393	Line 393
   394	Line 394
   395	Line 395
   396	Line 396
   397	Line 397
   398	Line 398
   399	Line 399
   400	Line 400
   401	Line 401
   402	Line 402
   403	Line 403
   404	Line 404
   405	Line 405
   406	Line 406
   407	Line 407
   408	Line 408
   409	Line 409
   410	Line 410
   411	Line 411
   412	Line 412
   413	Line 413
   414	Line 414
   415	Line 415
   416	Line 416
   417	Line 417
   418	Line 418
   419	Line 419
   420	Line 420
   421	Line 421
   422	Line 422
   423	Line 423
   424	Line 424
   425	Line 425
   426	Line 426
   427	Line 427
   428	Line 428
   429	Line 429
   430	Line 430
   431	Line 431
   432	Line 432
   433	Line 433
   434	Line 434
   435	Line 435
   436	Line 436
   437	Line 437
   438	Line 438
   439	Line 439
   440	Line 440
   441	Line 441
   442	Line 442
   443	Line 443
   444	Line 444
   445	Line 445
   446	Line 446
   447	Line 447
   448	Line 448
   449	Line 449
   450	Line 450
   451	Line 451
   452	Line 452
   453	Line 453
   454	Line 454
   455	Line 455
   456	Line 456
   457	Line 457
   458	Line 458
   459	Line 459
   460	Line 460
   461	Line 461
   462	Line 462
   463	Line 463
   464	Line 464
   465	Line 465
   466	Line 466
   467	Line 467
   468	Line 468
   469	Line 469
   470	Line 470
   471	Line 471
   472	Line 472
   473	Line 473
   474	Line 474
   475	Line 475
   476	Line 476
   477	Line 477
   478	Line 478
   479	Line 479
   480	Line 480
   481	Line 481
   482	Line 482
   483	Line 483
   484	Line 484
   485	Line 485
   486	Line 486
   487	Line 487
   488	Line 488
   489	Line 489
   490	Line 490
   491	Line 491
   492	Line 492
   493	Line 493
   494	Line 494
   495	Line 495
   496	Line 496
   497	Line 497
   498	Line 498
   499	Line 499
   500	Line 500
   501	Line 501
   502	Line 502
   503	Line 503
   504	Line 504
   505	Line 505
   506	Line 506
   507	Line 507
   508	Line 508
   509	Line 509
   510	Line 510
   511	Line 511
   512	Line 512
   513	Line 513
   514	Line 514
   515	Line 515
   516	Line 516
   517	Line 517
   518	Line 518
   519	Line 519
   520	Line 520
   521	Line 521
   522	Line 522
   523	Line 523
   524	Line 524
   525	Line 525
   526	Line 526
   527	Line 527
   528	Line 528
   529	Line 529
   530	Line 530
   531	Line 531
   532	Line 532
   533	Line 533
   534	Line 534
   535	Line 535
   536	Line 536
   537	Line 537
   538	Line 538
   539	Line 539
   540	Line 540
   541	Line 541
   542	Line 542
   543	Line 543
   544	Line 544
   545	Line 545
   546	Line 546
   547	Line 547
   548	Line 548
   549	Line 549
   550	Line 550
   551	Line 551
   552	Line 552
   553	Line 553
   554	Line 554
   555	Line 555
   556	Line 556
   557	Line 557
   558	Line 558
   559	Line 559
   560	Line 560
   561	Line 561
   562	Line 562
   563	Line 563
   564	Line 564
   565	Line 565
   566	Line 566
   567	Line 567
   568	Line 568
   569	Line 569
   570	Line 570
   571	Line 571
   572	Line 572
   573	Line 573
   574	Line 574
   575	Line 575
   576	Line 576
   577	Line 577
   578	Line 578
   579	Line 579
   580	Line 580
   581	Line 581
   582	Line 582
   583	Line 583
   584	Line 584
   585	Line 585
   586	Line 586
   587	Line 587
   588	Line 588
   589	Line 589
   590	Line 590
   591	Line 591
   592	Line 592
   593	Line 593
   594	Line 594
   595	Line 595
   596	Line 596
   597	Line 597
   598	Line 598
   599	Line 599
   600	Line 600
   601	Line 601
   602	Line 602
   603	Line 603
   604	Line 604
   605	Line 605
   606	Line 606
   607	Line 607
   608	Line 608
   609	Line 609
   610	Line 610
   611	Line 611
   612	Line 612
   613	Line 613
   614	Line 614
   615	Line 615
   616	Line 616
   617	Line 617
   618	Line 618
   619	Line 619
   620	Line 620
   621	Line 621
   622	Line 622
   623	Line 623
   624	Line 624
   625	Line 625
   626	Line 626
   627	Line 627
   628	Line 628
   629	Line 629
   630	Line 630
   631	Line 631
   632	Line 632
   633	Line 633
   634	Line 634
   635	Line 635
   636	Line 636
   637	Line 637
   638	Line 638
   639	Line 639
   640	Line 640
   641	Line 641
   642	Line 642
   643	Line 643
   644	Line 644
   645	Line 645
   646	Line 646
   647	Line 647
   648	Line 648
   649	Line 649
   650	Line 650
   651	Line 651
   652	Line 652
   653	Line 653
   654	Line 654
   655	Line 655
   656	Line 656
   657	Line 657
   658	Line 658
   659	Line 659
   660	Line 660
   661	Line 661
   662	Line 662
   663	Line 663
   664	Line 664
   665	Line 665
   666	Line 666
   667	Line 667
   668	Line 668
   669	Line 669
   670	Line 670
   671	Line 671
   672	Line 672
   673	Line 673
   674	Line 674
   675	Line 675
   676	Line 676
   677	Line 677
   678	Line 678
   679	Line 679
   680	Line 680
   681	Line 681
   682	Line 682
   683	Line 683
   684	Line 684
   685	Line 685
   686	Line 686
   687	Line 687
   688	Line 688
   689	Line 689
   690	Line 690
   691	Line 691
   692	Line 692
   693	Line 693
   694	Line 694
   695	Line 695
   696	Line 696
   697	Line 697
   698	Line 698
   699	Line 699
   700	Line 700
   701	Line 701
   702	Line 702
   703	Line 703
   704	Line 704
   705	Line 705
   706	Line 706
   707	Line 707
   708	Line 708
   709	Line 709
   710	Line 710
   711	Line 711
   712	Line 712
   713	Line 713
   714	Line 714
   715	Line 715
   716	Line 716
   717	Line 717
   718	Line 718
   719	Line 719
   720	Line 720
   721	Line 721
   722	Line 722
   723	Line 723
   724	Line 724
   725	Line 725
   726	Line 726
   727	Line 727
   728	Line 728
   729	Line 729
   730	Line 730
   731	Line 731
   732	Line 732
   733	Line 733
   734	Line 734
   735	Line 735
   736	Line 736
   737	Line 737
   738	Line 738
   739	Line 739
   740	Line 740
   741	Line 741
   742	Line 742
   743	Line 743
   744	Line 744
   745	Line 745
   746	Line 746
   747	Line 747
   748	Line 748
   749	Line 749
   750	Line 750
   751	Line 751
   752	Line 752
   753	Line 753
   754	Line 754
   755	Line 755
   756	Line 756
   757	Line 757
   758	Line 758
   759	Line 759
   760	Line 760
   761	Line 761
   762	Line 762
   763	Line 763
   764	Line 764
   765	Line 765
   766	Line 766
   767	Line 767
   768	Line 768
   769	Line 769
   770	Line 770
   771	Line 771
   772	Line 772
   773	Line 773
   774	Line 774
   775	Line 775
   776	Line 776
   777	Line 777
   778	Line 778
   779	Line 779
   780	Line 780
   781	Line 781
   782	Line 782
   783	Line 783
   784	Line 784
   785	Line 785
   786	Line 786
   787	Line 787
   788	Line 788
   789	Line 789
   790	Line 790
   791	Line 791
   792	Line 792
   793	Line 793
   794	Line 794
   795	Line 795
   796	Line 796
   797	Line 797
   798	Line 798
   799	Line 799
   800	Line 800
   801	Line 801
   802	Line 802
   803	Line 803
   804	Line 804
   805	Line 805
   806	Line 806
   807	Line 807
   808	Line 808
   809	Line 809
   810	Line 810
   811	Line 811
   812	Line 812
   813	Line 813
   814	Line 814
   815	Line 815
   816	Line 816
   817	Line 817
   818	Line 818
   819	Line 819
   820	Line 820
   821	Line 821
   822	Line 822
   823	Line 823
   824	Line 824
   825	Line 825
   826	Line 826
   827	Line 827
   828	Line 828
   829	Line 829
   830	Line 830
   831	Line 831
   832	Line 832
   833	Line 833
   834	Line 834
   835	Line 835
   836	Line 836
   837	Line 837
   838	Line 838
   839	Line 839
   840	Line 840
   841	Line 841
   842	Line 842
   843	Line 843
   844	Line 844
   845	Line 845
   846	Line 846
   847	Line 847
   848	Line 848
   849	Line 849
   850	Line 850
   851	Line 851
   852	Line 852
   853	Line 853
   854	Line 854
   855	Line 855
   856	Line 856
   857	Line 857
   858	Line 858
   859	Line 859
   860	Line 860
   861	Line 861
   862	Line 862
   863	Line 863
   864	Line 864
   865	Line 865
   866	Line 866
   867	Line 867
   868	Line 868
   869	Line 869
   870	Line 870
   871	Line 871
   872	Line 872
   873	Line 873
   874	Line 874
   875	Line 875
   876	Line 876
   877	Line 877
   878	Line 878
   879	Line 879
   880	Line 880
   881	Line 881
   882	Line 882
   883	Line 883
   884	Line 884
   885	Line 885
   886	Line 886
   887	Line 887
   888	Line 888
   889	Line 889
   890	Line 890
   891	Line 891
   892	Line 892
   893	Line 893
   894	Line 894
   895	Line 895
   896	Line 896
   897	Line 897
   898	Line 898
   899	Line 899
   900	Line 900
   901	Line 901
   902	Line 902
   903	Line 903
   904	Line 904
   905	Line 905
   906	Line 906
   907	Line 907
   908	Line 908
   909	Line 909
   910	Line 910
   911	Line 911
   912	Line 912
   913	Line 913
   914	Line 914
   915	Line 915
   916	Line 916
   917	Line 917
   918	Line 918
   919	Line 919
   920	Line 920
   921	Line 921
   922	Line 922
   923	Line 923
   924	Line 924
   925	Line 925
   926	Line 926
   927	Line 927
   928	Line 928
   929	Line 929
   930	Line 930
   931	Line 931
   932	Line 932
   933	Line 933
   934	Line 934
   935	Line 935
   936	Line 936
   937	Line 937
   938	Line 938
   939	Line 939
   940	Line 940
   941	Line 941
   942	Line 942
   943	Line 943
   944	Line 944
   945	Line 945
   946	Line 946
   947	Line 947
   948	Line 948
   949	Line 949
   950	Line 950
   951	Line 951
   952	Line 952
   953	Line 953
   954	Line 954
   955	Line 955
   956	Line 956
   957	Line 957
   958	Line 958
   959	Line 959
   960	Line 960
   961	Line 961
   962	Line 962
   963	Line 963
   964	Line 964
   965	Line 965
   966	Line 966
   967	Line 967
   968	Line 968
   969	Line 969
   970	Line 970
   971	Line 971
   972	Line 972
   973	Line 973
   974	Line 974
   975	Line 975
   976	Line 976
   977	Line 977
   978	Line 978
   979	Line 979
   980	Line 980
   981	Line 981
   982	Line 982
   983	Line 983
   984	Line 984
   985	Line 985
   986	Line 986
   987	Line 987
   988	Line 988
   989	Line 989
   990	Line 990
   991	Line 991
   992	Line 992
   993	Line 993
   994	Line 994
   995	Line 995
   996	Line 996
   997	Line 997
   998	Line 998
   999	Line 999
  1000	Line 1000
... (file truncated, showing 1000 of 1099 lines)""",
        )

    def test_normalize_result(self):
        """Test the normalize_result function"""
        # Test with a path containing the temp dir
        test_string = f"Error: File does not exist: {self.temp_dir.name}/some/path.txt"
        normalized = self.normalize_result(test_string)
        self.assertEqual(
            normalized,
            "Error: File does not exist: /tmp/test_dir/some/path.txt",
        )

        # Test with multiple occurrences of the temp dir
        test_string = f"Path1: {self.temp_dir.name}/file1.txt, Path2: {self.temp_dir.name}/file2.txt"
        normalized = self.normalize_result(test_string)
        self.assertEqual(
            normalized,
            "Path1: /tmp/test_dir/file1.txt, Path2: /tmp/test_dir/file2.txt",
        )

        # Test with a string that doesn't contain the temp dir
        test_string = "This string doesn't contain a temp dir path"
        normalized = self.normalize_result(test_string)
        self.assertEqual(normalized, test_string)


if __name__ == "__main__":
    unittest.main()
